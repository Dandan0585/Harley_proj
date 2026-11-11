"""
State de Compras (Entrada de Mercadoria + Itens de Compra em Estoque).

Este é o padrão a seguir para telas de "cabeçalho + itens" (a mesma ideia
se repete em `os_state.py` para Ordens de Serviço): a compra inteira é
montada em memória (`itens_atual`) e só é gravada no banco de uma vez,
em `finalizar_compra`, quando o usuário confirma: primeiro soma no estoque
(`estoque.movimentar`, protegido contra vendas simultâneas), depois cria o
cabeçalho (EntradaMercadoria) e uma linha (ItemCompraEstoque) por item. Se
algo falhar no meio, o que foi feito é desfeito. Excluir uma compra retira
do estoque o que ela tinha somado.

Cada compra tem uma descrição (campo `descricao` de entrada_mercadoria): ao
finalizar, ela é montada a partir dos itens ("2x Pneu..., 10x Óleo...") e
depois pode ser reescrita pela equipe na lista de compras. Compras antigas,
sem descrição gravada, mostram a descrição montada pelos itens.

Dados vêm do backend Xano.
"""

import asyncio
import logging

import reflex as rx

from .. import estoque
from .. import xano_client as xano
from ..validacao import inteiro, numero
from .auth_state import AuthState

log = logging.getLogger("harley_store.compras")

TABELA_ENTRADA = "entrada_mercadoria"
TABELA_ITENS = "itens_compra_estoque"
TABELA_FORNECEDORES = "fornecedores"
TABELA_PRODUTOS = "produtos"
MAX_DESCRICAO = 500


def descricao_dos_itens(itens: list[tuple[str, int]]) -> str:
    """[(nome do produto, quantidade)] -> "2x Pneu Traseiro; 10x Óleo 10W30"."""
    return "; ".join(f"{qtd}x {nome}" for nome, qtd in itens)


class ComprasState(rx.State):
    historico: list[dict] = []

    fornecedores_opcoes: list[str] = []
    produtos_opcoes: list[str] = []

    fornecedor_selecionado: str = ""
    itens_atual: list[dict] = []  # [{produto_id, produto_nome, quantidade, valor_unitario, subtotal}]

    item_produto_selecionado: str = ""
    item_quantidade: str = "1"
    item_valor_unitario: str = "0.00"

    erro_compra: str = ""

    # edição da descrição de uma compra já registrada (diálogo)
    descricao_compra_id: str = ""
    descricao_texto: str = ""
    erro_descricao: str = ""

    @rx.var
    def total_atual(self) -> str:
        total = sum(float(item["subtotal"]) for item in self.itens_atual)
        return f"{total:.2f}"

    @rx.event
    async def carregar(self):
        # As 4 tabelas são buscadas em paralelo.
        fornecedores, produtos, entradas_todas, itens = await asyncio.gather(
            xano.listar(TABELA_FORNECEDORES), xano.listar(TABELA_PRODUTOS),
            xano.listar(TABELA_ENTRADA), xano.listar(TABELA_ITENS),
        )
        fornecedores.sort(key=lambda f: (f.get("nome_fornecedor") or "").lower())
        produtos.sort(key=lambda p: (p.get("nome_produto") or "").lower())
        self.fornecedores_opcoes = [f"{f['id']} - {f['nome_fornecedor']}" for f in fornecedores]
        self.produtos_opcoes = [f"{p['id']} - {p['nome_produto']}" for p in produtos]
        # seleções que deixaram de existir (registro excluído) são descartadas
        if self.fornecedor_selecionado not in self.fornecedores_opcoes:
            self.fornecedor_selecionado = self.fornecedores_opcoes[0] if self.fornecedores_opcoes else ""
        if self.item_produto_selecionado not in self.produtos_opcoes:
            self.item_produto_selecionado = self.produtos_opcoes[0] if self.produtos_opcoes else ""

        nomes_fornecedor = {f["id"]: f["nome_fornecedor"] for f in fornecedores}
        nomes_produto = {p["id"]: p.get("nome_produto") or f"produto {p['id']}" for p in produtos}

        entradas = sorted(entradas_todas, key=lambda e: e.get("data_entrada") or 0, reverse=True)[:30]
        itens_por_entrada: dict[int, list[tuple[str, int]]] = {}
        for item in itens:
            nome = nomes_produto.get(item.get("id_produto"), "(produto excluído)")
            itens_por_entrada.setdefault(item["id_entrada"], []).append((nome, int(item.get("quantidade") or 0)))

        self.historico = [
            {
                "id": str(e["id"]),
                "data_entrada": xano.epoch_ms_para_datetime(e["data_entrada"]).strftime("%d/%m/%Y %H:%M"),
                "fornecedor_nome": nomes_fornecedor.get(e["id_fornecedor"], "—"),
                "valor_total": f"{float(e.get('valor_total') or 0):.2f}",
                "qtd_itens": str(len(itens_por_entrada.get(e["id"], []))),
                # gravada pela equipe; sem ela, montada pelos itens da compra
                "descricao": (e.get("descricao") or "").strip()
                or descricao_dos_itens(itens_por_entrada.get(e["id"], [])) or "—",
            }
            for e in entradas
        ]

    @rx.event
    def adicionar_item(self):
        self.erro_compra = ""
        if not self.item_produto_selecionado:
            self.erro_compra = "Escolha o produto (cadastre-o antes em Produtos, se ainda não existir)."
            return
        try:
            quantidade = inteiro(self.item_quantidade)
            valor_unitario = numero(self.item_valor_unitario)
        except ValueError:
            self.erro_compra = "Quantidade e valor unitário precisam ser números válidos."
            return
        if quantidade <= 0:
            self.erro_compra = "A quantidade precisa ser maior que zero."
            return
        if valor_unitario < 0:
            self.erro_compra = "O valor unitário não pode ser negativo."
            return

        produto_id, produto_nome = self.item_produto_selecionado.split(" - ", 1)
        self.itens_atual = self.itens_atual + [
            {
                "produto_id": produto_id,
                "produto_nome": produto_nome,
                "quantidade": str(quantidade),
                "valor_unitario": f"{valor_unitario:.2f}",
                "subtotal": f"{quantidade * valor_unitario:.2f}",
            }
        ]
        self.item_quantidade = "1"
        self.item_valor_unitario = "0.00"

    @rx.event
    def remover_item(self, indice: int):
        self.itens_atual = [item for i, item in enumerate(self.itens_atual) if i != indice]

    @rx.event
    async def finalizar_compra(self):
        self.erro_compra = ""
        if not self.fornecedor_selecionado:
            self.erro_compra = "Selecione o fornecedor."
            return
        if not self.itens_atual:
            self.erro_compra = "Adicione ao menos um item à compra."
            return

        id_fornecedor = int(self.fornecedor_selecionado.split(" - ")[0])
        total = round(sum(float(item["subtotal"]) for item in self.itens_atual), 2)
        entradas: dict[int, int] = {}
        for item in self.itens_atual:
            pid = int(item["produto_id"])
            entradas[pid] = entradas.get(pid, 0) + int(item["quantidade"])

        # 1) soma no estoque (protegido contra vendas simultâneas)
        try:
            saldos = await estoque.movimentar(entradas)
        except estoque.ProdutoInexistente as erro:
            self.erro_compra = f"{erro} Remova o item e tente de novo."
            await self.carregar()
            return
        estorno = {pid: -qtd for pid, qtd in entradas.items()}

        # 2) cabeçalho e itens; se algo falhar, desfaz tudo
        entrada = None
        criados: list[int] = []
        try:
            entrada = await xano.criar(TABELA_ENTRADA, {
                "id_fornecedor": id_fornecedor,
                "data_entrada": xano.datetime_para_epoch_ms(),
                "valor_total": total,
                "descricao": descricao_dos_itens(
                    [(item["produto_nome"], int(item["quantidade"])) for item in self.itens_atual]
                )[:MAX_DESCRICAO],
            })
            for item in self.itens_atual:
                gravado = await xano.criar(TABELA_ITENS, {
                    "id_entrada": entrada["id"],
                    "id_produto": int(item["produto_id"]),
                    "quantidade": int(item["quantidade"]),
                    "valor_unitario": float(item["valor_unitario"]),
                })
                criados.append(int(gravado["id"]))
        except Exception:
            log.exception("falha ao gravar a compra; desfazendo")
            for item_id in criados:
                try:
                    await xano.excluir(TABELA_ITENS, item_id)
                except Exception:
                    log.exception("nao foi possivel apagar o item %s da compra incompleta", item_id)
            if entrada:
                try:
                    await xano.excluir(TABELA_ENTRADA, int(entrada["id"]))
                except Exception:
                    log.exception("nao foi possivel apagar a compra incompleta %s", entrada.get("id"))
            try:
                await estoque.movimentar(estorno)
            except Exception:
                log.exception("nao foi possivel estornar o estoque da compra incompleta: %s", estorno)
                self.erro_compra = ("A compra não pôde ser gravada e o estoque NÃO pôde ser corrigido. "
                                    "Confira o estoque dos produtos lançados.")
                return
            self.erro_compra = "A compra não pôde ser gravada (falha de conexão). Nada foi alterado; tente de novo."
            return

        usuario = (await self.get_state(AuthState)).usuario_logado
        await estoque.registrar_historico(entradas, saldos, "COMPRA", int(entrada["id"]), usuario)
        self.itens_atual = []
        await self.carregar()
        return rx.toast.success(f"Compra nº {entrada['id']} registrada; estoque atualizado.")

    @rx.event
    def editar_descricao(self, entrada_id: str, descricao: str):
        self.descricao_compra_id = entrada_id
        self.descricao_texto = "" if descricao == "—" else descricao
        self.erro_descricao = ""

    @rx.event
    def fechar_descricao(self, aberto: bool = False):
        if not aberto:
            self.descricao_compra_id = ""

    @rx.event
    async def salvar_descricao(self):
        texto = " ".join(self.descricao_texto.split())
        if len(texto) > MAX_DESCRICAO:
            self.erro_descricao = f"A descrição pode ter no máximo {MAX_DESCRICAO} caracteres."
            return
        entrada_id = int(self.descricao_compra_id)
        registro = await xano.buscar_direto(TABELA_ENTRADA, entrada_id)
        if registro is None:
            self.descricao_compra_id = ""
            await self.carregar()
            return rx.toast.error("Essa compra não existe mais (foi excluída por outra pessoa).")
        # PATCH do Xano exige o registro completo
        dados = {k: v for k, v in registro.items() if k != "id"}
        dados["descricao"] = texto or None
        gravado = await xano.atualizar(TABELA_ENTRADA, entrada_id, dados)
        if "descricao" not in gravado:
            log.error("entrada_mercadoria sem o campo descricao no Xano")
            self.erro_descricao = ("O banco ainda não tem o campo de descrição. "
                                   "Rode scripts/aplicar_xano.ps1 e tente de novo.")
            return
        self.descricao_compra_id = ""
        await self.carregar()
        return rx.toast.success(f"Descrição da compra nº {entrada_id} atualizada.")

    @rx.event
    async def excluir_entrada(self, entrada_id: str):
        """Exclui a compra e seus itens, retirando do estoque o que ela tinha
        somado. Se parte já foi vendida (o estoque ficaria negativo), recusa."""
        entrada_id_int = int(entrada_id)
        itens = [i for i in await xano.listar(TABELA_ITENS) if i.get("id_entrada") == entrada_id_int]
        existentes = {p["id"] for p in await xano.listar(TABELA_PRODUTOS)}
        estorno: dict[int, int] = {}
        for item in itens:
            pid = int(item.get("id_produto") or 0)
            if pid in existentes:
                estorno[pid] = estorno.get(pid, 0) - int(item.get("quantidade") or 0)
        try:
            saldos = await estoque.movimentar(estorno)
        except estoque.EstoqueInsuficiente as erro:
            return rx.toast.error(
                "Esta compra não pode ser excluída: parte dos produtos já saiu do estoque ("
                + ", ".join(erro.produtos) + "). Nada foi alterado."
            )
        try:
            for item in itens:
                await xano.excluir(TABELA_ITENS, item["id"])
            await xano.excluir(TABELA_ENTRADA, entrada_id_int)
        except Exception:
            log.exception("falha ao excluir a compra %s; devolvendo o estoque", entrada_id_int)
            try:
                await estoque.movimentar({pid: -q for pid, q in estorno.items()})
            except Exception:
                log.exception("nao foi possivel devolver o estoque da compra %s", entrada_id_int)
            await self.carregar()
            return rx.toast.error("A compra não pôde ser excluída por completo (falha de conexão). Tente de novo.")
        usuario = (await self.get_state(AuthState)).usuario_logado
        await estoque.registrar_historico(estorno, saldos, "EXCLUSAO_COMPRA", entrada_id_int, usuario)
        await self.carregar()
        return rx.toast.success(f"Compra nº {entrada_id} excluída; o estoque foi ajustado.")
