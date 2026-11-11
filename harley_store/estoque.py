"""
Movimentação de estoque protegida contra operações simultâneas.

TODA alteração de saldo passa por aqui: vendas e cancelamentos
(vendas_servico.py), peças lançadas em OS e exclusão de OS (os_state.py),
compras e exclusão de compras (compras_state.py) usam `movimentar()`, e a
edição do cadastro de produto usa `atualizar_produto()`. Sem isso, duas
operações no mesmo produto ao mesmo tempo liam o mesmo saldo e gravavam por
cima uma da outra, e uma das movimentações se perdia.

Como funciona:
- uma trava (asyncio.Lock) por produto, adquiridas sempre em ordem crescente
  de id: duas operações com os mesmos produtos nunca ficam esperando uma pela
  outra em ciclo (deadlock);
- com as travas na mão, cada produto é relido DIRETO do Xano (sem cache);
- se qualquer produto ficar com estoque negativo, nada é alterado;
- os PATCHs são aplicados um a um; se um falhar, os já aplicados são desfeitos.

PRESSUPOSTO IMPORTANTE: as travas vivem na memória de UM processo. A produção
roda com 1 worker de backend (sem Redis, o Reflex 0.7 usa 1 worker). Se um
dia houver Redis ou mais workers, esta proteção precisa migrar para o Xano
(função com transação). O ambiente de desenvolvimento é outro processo: não é
protegido contra a produção, por isso a regra de testes do README.
"""

from __future__ import annotations

import asyncio
import logging

from . import xano_client as xano

log = logging.getLogger("harley_store.estoque")

TABELA_PRODUTOS = "produtos"

_travas: dict[int, asyncio.Lock] = {}


class EstoqueInsuficiente(Exception):
    """Algum produto ficaria com estoque negativo. `produtos` = nomes."""

    def __init__(self, produtos: list[str]):
        self.produtos = produtos
        super().__init__("Estoque insuficiente: " + ", ".join(produtos))


class ProdutoInexistente(Exception):
    pass


async def _ler_produto(produto_id: int) -> dict | None:
    """Leitura direta do Xano, sem cache: dentro da trava o saldo precisa ser o real."""
    resposta = await xano._request("GET", f"{xano.BASE_URL}/{TABELA_PRODUTOS}/{produto_id}")
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    return resposta.json()


async def _gravar_estoque(produto: dict, novo_estoque: int) -> None:
    dados = {k: v for k, v in produto.items() if k != "id"}  # PATCH do Xano exige o registro completo
    dados["estoque_qtd"] = novo_estoque
    await xano.atualizar(TABELA_PRODUTOS, produto["id"], dados)


async def atualizar_produto(produto_id: int, dados: dict, variacao_estoque: int) -> dict:
    """Edição do cadastro de um produto sem perder movimentações simultâneas.

    O formulário de Produtos mostra o saldo lido ao abrir a edição. Gravar
    esse número direto apagaria uma venda ou compra feita enquanto o
    formulário estava aberto. Por isso a tela manda a VARIAÇÃO que o
    funcionário fez no campo (novo - lido), e ela é aplicada, sob a mesma
    trava das vendas, sobre o saldo atual relido do Xano.
    Levanta ProdutoInexistente ou EstoqueInsuficiente (nada é alterado)."""
    produto_id = int(produto_id)
    async with _travas.setdefault(produto_id, asyncio.Lock()):
        atual = await _ler_produto(produto_id)
        if atual is None:
            raise ProdutoInexistente(f"Produto {produto_id} não existe mais.")
        novo_estoque = (atual.get("estoque_qtd") or 0) + int(variacao_estoque)
        if novo_estoque < 0:
            raise EstoqueInsuficiente([f"{atual['nome_produto']} (há {atual.get('estoque_qtd') or 0})"])
        registro = {k: v for k, v in atual.items() if k != "id"}
        registro.update({k: v for k, v in dados.items() if k != "estoque_qtd"})
        registro["estoque_qtd"] = novo_estoque
        return await xano.atualizar(TABELA_PRODUTOS, produto_id, registro)


async def movimentar(ajustes: dict[int, int]) -> dict[int, int]:
    """Aplica variações de estoque: {id_produto: variação}. Negativa = baixa,
    positiva = devolução. Tudo ou nada: levanta EstoqueInsuficiente (nada é
    alterado) ou a exceção da falha de gravação (o que foi aplicado é desfeito).
    Devolve o saldo final de cada produto ({id: saldo}), para o histórico."""
    ajustes = {int(pid): int(qtd) for pid, qtd in ajustes.items() if int(qtd) != 0}
    if not ajustes:
        return {}
    ordem = sorted(ajustes)
    travas = [_travas.setdefault(pid, asyncio.Lock()) for pid in ordem]
    for trava in travas:
        await trava.acquire()
    try:
        produtos = {}
        for pid in ordem:
            produto = await _ler_produto(pid)
            if produto is None:
                raise ProdutoInexistente(f"Produto {pid} não existe mais.")
            produtos[pid] = produto

        faltando = [
            f"{produtos[pid]['nome_produto']} (há {produtos[pid]['estoque_qtd']})"
            for pid in ordem
            if (produtos[pid].get("estoque_qtd") or 0) + ajustes[pid] < 0
        ]
        if faltando:
            raise EstoqueInsuficiente(faltando)

        aplicados: list[int] = []
        saldos: dict[int, int] = {}
        try:
            for pid in ordem:
                anterior = produtos[pid].get("estoque_qtd") or 0
                await _gravar_estoque(produtos[pid], anterior + ajustes[pid])
                aplicados.append(pid)
                saldos[pid] = anterior + ajustes[pid]
        except Exception:
            # desfaz, na medida do possível, o que já tinha sido gravado
            for pid in reversed(aplicados):
                try:
                    await _gravar_estoque(produtos[pid], produtos[pid].get("estoque_qtd") or 0)
                except Exception:
                    pass
            raise
        return saldos
    finally:
        for trava in reversed(travas):
            trava.release()


# ------------------------------------------------------------ histórico

TABELA_HISTORICO = "movimentacoes_estoque"


async def registrar_historico(
    ajustes: dict[int, int], saldos: dict[int, int], origem: str, referencia_id: int = 0, usuario: str = ""
) -> None:
    """Grava no histórico (tabela movimentacoes_estoque) as movimentações já
    aplicadas. Nunca falha: o saldo é o que importa; se o histórico não puder
    ser gravado, fica só o aviso no log."""
    for pid, qtd in ajustes.items():
        if not int(qtd):
            continue
        try:
            await xano.criar(TABELA_HISTORICO, {
                "produto_id": int(pid),
                "quantidade": int(qtd),
                "saldo_apos": saldos.get(int(pid)),
                "origem": origem,
                "referencia_id": int(referencia_id or 0),
                "usuario": usuario or "",
            })
        except Exception as erro:
            log.warning("historico de estoque nao gravado (%s, produto %s): %r", origem, pid, erro)
