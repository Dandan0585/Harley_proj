"""
Regras de negócio de vendas: registrar uma venda com vários itens e cancelar
vendas (uma ou várias), devolvendo o estoque.

Separado do state da tela (state/vendas_state.py) para poder ser testado
diretamente. Ordem das operações e motivos: ver
openspec/changes/vendas-com-itens-e-cancelamento/design.md (D3 e D4).

Tabelas no Xano:
- transacoes: + status ("ATIVA"/"CANCELADA"; vazio = ativa, vendas antigas),
  data_cancelamento, motivo_cancelamento;
- itens_transacao: transacao_id, produto_id (0 = item avulso), moto_id (moto
  da loja vendida no item), descricao, quantidade, valor_unitario. Os nomes
  seguem a convenção do projeto (xano/knowledge/agents.md: chave estrangeira
  com sufixo _id). ATENÇÃO: o Xano ignora em silêncio um campo com nome
  errado, gravando 0; use as constantes.

Moto da loja vendida no Balcão (change venda-de-motos-no-balcao, design D1 a
D6): o item tem produto_id 0 e moto_id; preço e descrição vêm do cadastro da
moto, relido aqui. A moto fica "Vendida" e conta no Painel pelo próprio
cadastro, e o item da moto não conta em produtos.

Pagamento (change pagamento-de-vendas-pelo-asaas, design D3 a D7): a venda
grava a forma de pagamento; nas formas pelo Asaas, a cobrança é gerada
depois do registro (pagamentos_servico), e uma falha nela NÃO desfaz a venda.
O cancelamento também cancela a cobrança em aberto.
"""

from __future__ import annotations

import asyncio
import re

from . import asaas_client, email_clientes, estoque
from . import pagamentos_servico as pagamentos
from . import xano_client as xano
from .constantes import TIPOS_VENDA

TABELA = "transacoes"
TABELA_ITENS = "itens_transacao"
TABELA_MOTOS = "motos"                     # motos da loja
TABELA_MOTOS_CLIENTES = "motos_clientes"
TABELA_CLIENTES = "clientes"
TABELA_OS = "ordens_servico"
STATUS_ATIVA = "ATIVA"
STATUS_CANCELADA = "CANCELADA"
MOTIVO_FALHA = "Falha ao registrar os itens da venda"
CAMPO_VENDA = "transacao_id"    # itens_transacao -> transacoes
CAMPO_PRODUTO = "produto_id"    # itens_transacao -> produtos (0 = avulso)
CAMPO_MOTO = "moto_id"          # itens_transacao -> motos (moto da loja)

MOTO_VENDIDA = "Vendida"
MOTO_EM_ESTOQUE = "Em estoque"
MOTOS_FORA_DA_VENDA = {MOTO_VENDIDA, "Indisponível"}  # situações que o Balcão não vende
AVISO_XANO_DESATUALIZADO = (
    "O banco ainda não tem o campo que liga a venda à moto (itens_transacao.moto_id). "
    "Peça para aplicar a atualização com scripts\\aplicar_xano.ps1. Nada foi alterado."
)

_travas_venda = pagamentos.travas_venda  # a mesma trava da cobrança e da consulta do pagamento
_travas_moto: dict[int, asyncio.Lock] = {}


class FalhaVenda(Exception):
    """Erro com mensagem pronta para mostrar ao funcionário."""


def esta_cancelada(transacao: dict) -> bool:
    return (transacao.get("status") or "").strip().upper() == STATUS_CANCELADA


async def _ler_direto(caminho: str):
    """Leitura sem cache: usada dentro das travas, onde o dado precisa ser o atual."""
    resposta = await xano._request("GET", f"{xano.BASE_URL}/{caminho}")
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    return resposta.json()


async def _itens_da_venda(venda_id: int, venda_nova: bool = False) -> list[dict]:
    """Pelo cache: os itens de uma venda nunca mudam depois de criados, e toda
    criação feita pelo app já entra no cache (xano_client._aplicar_no_cache).
    Se uma venda NOVA (com status) não tiver itens no cache, ela pode ter sido
    registrada por outro processo (ex.: desenvolvimento): confere direto no
    Xano antes de concluir que não há o que devolver ao estoque."""
    itens = [i for i in await xano.listar(TABELA_ITENS) if int(i.get(CAMPO_VENDA) or 0) == venda_id]
    if not itens and venda_nova:
        todos = await _ler_direto(TABELA_ITENS) or []
        itens = [i for i in todos if int(i.get(CAMPO_VENDA) or 0) == venda_id]
    return itens


async def _marcar_cancelada(venda: dict, motivo: str) -> dict:
    # PATCH do Xano exige o registro completo (inclusive os campos de pagamento)
    dados = {k: v for k, v in venda.items() if k != "id"}
    dados["status"] = STATUS_CANCELADA
    dados["data_cancelamento"] = xano.datetime_para_epoch_ms()
    dados["motivo_cancelamento"] = (motivo or "").strip() or None
    gravada = await xano.atualizar(TABELA, venda["id"], dados)
    return {**venda, **dados, **(gravada or {}), "id": venda["id"]}


# ------------------------------------------------------------ moto da loja
# Funções puras (testadas em tests/test_venda_de_moto.py): a tela usa as
# mesmas para avisar antes, e o servidor confere de novo com a moto relida.

def nome_moto(moto: dict) -> str:
    return " ".join(str(p) for p in (moto.get("marca"), moto.get("modelo"), moto.get("ano")) if p)


def problema_moto(moto: dict | None) -> str:
    """Por que a moto da loja não pode ser vendida no Balcão ("" = pode)."""
    if not moto:
        return "Essa moto não existe mais no estoque."
    nome = nome_moto(moto)
    situacao = moto.get("status") or MOTO_EM_ESTOQUE
    if situacao == MOTO_VENDIDA:
        return f"A moto {nome} já foi vendida."
    if situacao in MOTOS_FORA_DA_VENDA:
        return f"A moto {nome} está {situacao} e não pode ser vendida."
    if not (moto.get("chassi") or "").strip():
        return f"Para vender a moto {nome}, informe o chassi no cadastro dela (Produtos > Motos)."
    if not float(moto.get("preco_venda") or 0) > 0:
        return f"Informe o preço de venda da moto {nome} no cadastro dela (Produtos > Motos)."
    return ""


def descricao_moto(moto: dict) -> str:
    """Descrição do item da venda (vai no comprovante): modelo e identificação da moto."""
    titulo = " ".join(p for p in (nome_moto(moto), moto.get("cor") or "") if p)
    dados = [f"chassi {moto.get('chassi')}"]
    if moto.get("placa"):
        dados.append(f"placa {moto['placa']}")
    if moto.get("renavam"):
        dados.append(f"RENAVAM {moto['renavam']}")
    if moto.get("cilindrada"):
        dados.append(f"{moto['cilindrada']} cm³")
    dados.append(f"{int(moto.get('quilometragem') or 0):,} km".replace(",", "."))
    return f"Moto {titulo} — {', '.join(dados)}"


def _registro_moto(moto: dict, **mudancas) -> dict:
    # Registro COMPLETO: o PATCH do Xano zera o que não for enviado (inclusive as fotos).
    dados = {k: v for k, v in moto.items() if k not in ("id", "created_at", "updated_at")}
    dados.update(mudancas)
    return dados


def moto_vendida(moto: dict, id_cliente: int, data_ms: int) -> dict:
    return _registro_moto(moto, status=MOTO_VENDIDA, em_estoque=False, cliente_id=int(id_cliente),
                          data_saida=int(data_ms))


def moto_devolvida(moto: dict) -> dict:
    return _registro_moto(moto, status=MOTO_EM_ESTOQUE, em_estoque=True, cliente_id=0, data_saida=0)


def _placa(texto) -> str:
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def _chassi(texto) -> str:
    return re.sub(r"\s", "", texto or "").upper()


async def _itens_tem_campo_moto() -> bool:
    """O Xano já tem itens_transacao.moto_id? (Campo inexistente é ignorado em
    silêncio.) Os registros lidos trazem todos os campos da tabela; o cache
    pode ser de antes da atualização, então confere direto antes de recusar."""
    itens = await xano.listar(TABELA_ITENS)
    if not itens or CAMPO_MOTO in itens[0]:
        return True
    itens = await _ler_direto(TABELA_ITENS) or []
    return not itens or CAMPO_MOTO in itens[0]


async def _cadastrar_moto_do_cliente(moto: dict, id_cliente: int) -> tuple[int, str]:
    """Moto vendida -> Motos dos clientes, em nome do comprador (design D5).
    Devolve (id do cadastro ou 0, aviso)."""
    chassi, placa = _chassi(moto.get("chassi")), _placa(moto.get("placa"))
    registros = await xano.listar(TABELA_MOTOS_CLIENTES)
    existente = next((r for r in registros if _chassi(r.get("chassi")) == chassi), None)
    if existente:
        if int(existente.get("id_cliente") or 0) != int(id_cliente):
            await xano.atualizar(TABELA_MOTOS_CLIENTES, existente["id"], {
                "id_cliente": int(id_cliente),
                "modelo": existente.get("modelo") or moto.get("modelo") or "",
                "placa": existente.get("placa") or placa,
                "chassi": existente.get("chassi") or chassi,
                "imagem": existente.get("imagem") or None,
            })
        return int(existente["id"]), ""
    if not placa:
        return 0, "A moto não tem placa: cadastre-a em Motos dos clientes depois do emplacamento."
    if any(_placa(r.get("placa")) == placa for r in registros):
        return 0, f"Já existe em Motos dos clientes outra moto com a placa {placa}: confira o cadastro."
    novo = await xano.criar(TABELA_MOTOS_CLIENTES, {
        "id_cliente": int(id_cliente), "modelo": moto.get("modelo") or "", "placa": placa, "chassi": chassi,
        "imagem": None,
    })
    return int(novo["id"]), ""


async def _depois_da_venda_da_moto(venda: dict, moto: dict, id_cliente: int) -> list[str]:
    """Passos que não desfazem a venda (design D4): só geram avisos."""
    avisos = []
    try:
        id_moto_cliente, aviso = await _cadastrar_moto_do_cliente(moto, id_cliente)
        if aviso:
            avisos.append(aviso)
        if id_moto_cliente:
            dados = {k: v for k, v in venda.items() if k != "id"}  # PATCH do Xano exige o registro completo
            dados["id_moto_cliente"] = id_moto_cliente
            venda.update(await xano.atualizar(TABELA, venda["id"], dados))
    except Exception:
        avisos.append("A moto não pôde ser cadastrada em Motos dos clientes (falha de conexão): cadastre-a manualmente.")
    try:
        comprador = await xano.buscar(TABELA_CLIENTES, id_cliente)
        descricao = " ".join(p for p in (nome_moto(moto), moto.get("cor") or "") if p)
        if comprador and comprador.get("email") and email_clientes.parabens_compra(
                comprador.get("nome_cliente") or "", comprador["email"], descricao):
            avisos.append("E-mail de parabéns enviado ao cliente.")
    except Exception:
        pass  # o e-mail nunca desfaz a venda
    return avisos


# ---------------------------------------------------------------- registro

async def registrar_venda(
    tipo: str, id_funcionario: int, id_cliente: int, id_moto: int, itens: list[dict], usuario: str = "",
    forma_pagamento: str = pagamentos.NA_LOJA, vencimento: str = "",
) -> tuple[int, list[str]]:
    """itens: [{id_produto (0 = avulso), descricao, quantidade, valor_unitario}];
    a moto da loja vai como {id_moto} (descrição e valor vêm do cadastro dela).
    forma_pagamento: uma de pagamentos.FORMAS; vencimento (AAAA-MM-DD) nas formas pelo Asaas.
    Devolve (id da venda, avisos). Levanta FalhaVenda com mensagem para o usuário."""
    # Conferido aqui, e não só na tela: o tipo pode chegar direto pelo websocket.
    if tipo not in TIPOS_VENDA:
        raise FalhaVenda(f"Tipo de venda inválido: {tipo or '(vazio)'}. Use {', '.join(TIPOS_VENDA)}.")
    if not itens:
        raise FalhaVenda("Adicione ao menos um item à venda.")
    await _conferir_pagamento(forma_pagamento, vencimento, id_cliente)
    venda_id, avisos = await _registrar_itens(tipo, id_funcionario, id_cliente, id_moto, itens, usuario,
                                              forma_pagamento)
    if pagamentos.pelo_asaas(forma_pagamento):
        # depois do registro: uma falha aqui deixa a venda em "Falha na cobrança" (design D4)
        _, mensagem = await pagamentos.gerar_cobranca(venda_id, vencimento)
        avisos.append(mensagem)
    return venda_id, avisos


async def _conferir_pagamento(forma: str, vencimento: str, id_cliente: int) -> None:
    """Forma, vencimento e cliente conferidos ANTES de baixar o estoque (design D4, passo 1)."""
    problema = pagamentos.problema_forma(forma, vencimento, asaas_ligado=asaas_client.configurado())
    if problema:
        raise FalhaVenda(problema)
    if not pagamentos.pelo_asaas(forma):
        return
    try:
        cliente = await xano.buscar(TABELA_CLIENTES, id_cliente) if id_cliente else None
        campos_existem = await pagamentos.xano_tem_campos()
    except Exception:
        raise FalhaVenda("Não foi possível conectar ao banco. Nada foi alterado; tente de novo.")
    problema = pagamentos.problema_cliente(cliente)
    if problema:
        raise FalhaVenda(f"{problema} Nada foi alterado.")
    if not campos_existem:
        raise FalhaVenda("O banco ainda não tem os campos de pagamento (transacoes.forma_pagamento). Peça para "
                         "aplicar a atualização com scripts\\aplicar_xano.ps1. Nada foi alterado.")


async def _registrar_itens(
    tipo: str, id_funcionario: int, id_cliente: int, id_moto: int, itens: list[dict], usuario: str,
    forma_pagamento: str,
) -> tuple[int, list[str]]:
    motos = [int(i.get("id_moto") or 0) for i in itens if int(i.get("id_moto") or 0)]
    if not motos:
        return await _registrar(tipo, id_funcionario, id_cliente, id_moto, itens, usuario,
                                forma_pagamento=forma_pagamento)
    if len(motos) > 1:
        raise FalhaVenda("Só é possível vender uma moto da loja por venda.")
    if not id_cliente:
        raise FalhaVenda("Para vender uma moto da loja, escolha o cliente comprador.")

    # Uma venda por vez para a mesma moto: a segunda relê a moto já Vendida (design D4).
    async with _travas_moto.setdefault(motos[0], asyncio.Lock()):
        try:
            moto = await xano.buscar_direto(TABELA_MOTOS, motos[0])
            campo_existe = await _itens_tem_campo_moto()
        except Exception:
            raise FalhaVenda("Não foi possível conectar ao banco. Nada foi alterado; tente de novo.")
        problema = problema_moto(moto)
        if problema:
            raise FalhaVenda(problema)
        if not campo_existe:
            raise FalhaVenda(AVISO_XANO_DESATUALIZADO)
        # preço e descrição do cadastro, nunca os da tela (design D3)
        itens = [
            {"id_produto": 0, "id_moto": moto["id"], "descricao": descricao_moto(moto), "quantidade": 1,
             "valor_unitario": float(moto["preco_venda"])} if int(i.get("id_moto") or 0) else i
            for i in itens
        ]
        return await _registrar(tipo, id_funcionario, id_cliente, 0, itens, usuario, moto, forma_pagamento)


class _XanoDesatualizado(Exception):
    """O item da moto voltou sem moto_id: o campo não existe no Xano."""


async def _registrar(
    tipo: str, id_funcionario: int, id_cliente: int, id_moto: int, itens: list[dict], usuario: str,
    moto: dict | None = None, forma_pagamento: str = pagamentos.NA_LOJA,
) -> tuple[int, list[str]]:
    baixas: dict[int, int] = {}
    for item in itens:
        if int(item["id_produto"]):
            baixas[int(item["id_produto"])] = baixas.get(int(item["id_produto"]), 0) - int(item["quantidade"])
    total = round(sum(int(i["quantidade"]) * float(i["valor_unitario"]) for i in itens), 2)

    # 1) baixa todo o estoque, ou nada
    try:
        saldos = await estoque.movimentar(baixas)
    except estoque.EstoqueInsuficiente as erro:
        raise FalhaVenda("Estoque insuficiente: " + ", ".join(erro.produtos) + ". Nada foi alterado.")
    except estoque.ProdutoInexistente as erro:
        raise FalhaVenda(f"{erro} Remova o item e tente de novo.")
    except Exception:
        raise FalhaVenda("Não foi possível conectar ao banco. Nada foi alterado; tente de novo.")

    devolucao = {pid: -qtd for pid, qtd in baixas.items()}
    agora = xano.datetime_para_epoch_ms()

    # 2) cria a venda ativa
    try:
        venda = await xano.criar(TABELA, {
            "tipo_transacao": tipo,
            "id_funcionario": id_funcionario,
            "id_cliente": id_cliente,
            "id_moto_cliente": id_moto,
            "data_transacao": agora,
            "valor_total": total,
            "status": STATUS_ATIVA,
            "data_cancelamento": None,
            "motivo_cancelamento": None,
            "forma_pagamento": forma_pagamento,
            "situacao_pagamento": (pagamentos.SEM_COBRANCA if pagamentos.pelo_asaas(forma_pagamento)
                                   else pagamentos.NA_LOJA),
            "asaas_cobranca_id": None,
            "link_cobranca": None,
            "data_pagamento": None,
        })
    except Exception:
        await _devolver_sem_falhar(devolucao)
        raise FalhaVenda("A venda não pôde ser registrada (falha de conexão). O estoque foi devolvido; tente de novo.")

    # 3) grava os itens
    try:
        for item in itens:
            id_moto_item = int(item.get("id_moto") or 0)
            gravado = await xano.criar(TABELA_ITENS, {
                CAMPO_VENDA: venda["id"],
                CAMPO_PRODUTO: int(item["id_produto"]),
                CAMPO_MOTO: id_moto_item,
                "descricao": item["descricao"],
                "quantidade": int(item["quantidade"]),
                "valor_unitario": float(item["valor_unitario"]),
            })
            # O Xano ignora em silêncio campos com nome diferente do schema e
            # grava 0: confere que o item ficou mesmo ligado à venda (e à moto).
            if int(gravado.get(CAMPO_VENDA) or 0) != int(venda["id"]):
                raise RuntimeError(f"item gravado sem vínculo com a venda ({CAMPO_VENDA})")
            if id_moto_item and int(gravado.get(CAMPO_MOTO) or 0) != id_moto_item:
                raise _XanoDesatualizado()
    except _XanoDesatualizado:
        await _desfazer(venda, devolucao)
        raise FalhaVenda(f"{AVISO_XANO_DESATUALIZADO.replace(' Nada foi alterado.', '')} "
                         f"O estoque foi devolvido e a venda nº {venda['id']} ficou cancelada.")
    except Exception:
        await _desfazer(venda, devolucao)
        raise FalhaVenda(
            f"Os itens da venda nº {venda['id']} não puderam ser gravados (falha de conexão). "
            "O estoque foi devolvido e a venda ficou cancelada; registre-a de novo."
        )

    # 4) marca a moto da loja como Vendida (é o que a conta no Painel)
    if moto:
        try:
            await xano.atualizar(TABELA_MOTOS, moto["id"], moto_vendida(moto, id_cliente, agora))
        except Exception:
            await _desfazer(venda, devolucao)
            raise FalhaVenda(
                f"A moto não pôde ser marcada como vendida (falha de conexão). O estoque foi devolvido e "
                f"a venda nº {venda['id']} ficou cancelada; registre-a de novo."
            )

    await estoque.registrar_historico(baixas, saldos, "VENDA", int(venda["id"]), usuario)
    avisos = await _depois_da_venda_da_moto(venda, moto, id_cliente) if moto else []
    return int(venda["id"]), avisos


async def _desfazer(venda: dict, devolucao: dict[int, int]) -> None:
    """Venda que falhou no meio: devolve o estoque e deixa a venda cancelada."""
    await _devolver_sem_falhar(devolucao)
    try:
        await _marcar_cancelada(venda, MOTIVO_FALHA)
    except Exception:
        pass


async def _devolver_sem_falhar(ajustes: dict[int, int]) -> None:
    try:
        await estoque.movimentar(ajustes)
    except Exception:
        pass


# ------------------------------------------------------------ cancelamento

async def _devolver_moto(moto_id: int, venda: dict) -> str:
    """Moto da venda cancelada volta ao estoque (design D6). Devolve o aviso ("" = tudo certo)."""
    nome = f"nº {moto_id}"
    try:
        moto = await xano.buscar_direto(TABELA_MOTOS, moto_id)
        if moto is None:
            return f"A moto da loja nº {moto_id} não existe mais: confira o estoque de motos."
        nome = nome_moto(moto) or nome
        if moto.get("status") != MOTO_VENDIDA or int(moto.get("cliente_id") or 0) != int(venda.get("id_cliente") or 0):
            return f"A moto {nome} foi alterada depois da venda e não voltou ao estoque: confira em Produtos > Motos."
        await xano.atualizar(TABELA_MOTOS, moto_id, moto_devolvida(moto))
    except Exception:
        return f"A moto {nome} não pôde voltar ao estoque (falha de conexão): ajuste em Produtos > Motos."

    id_moto_cliente = int(venda.get("id_moto_cliente") or 0)
    if not id_moto_cliente:
        return ""
    try:
        registro = await xano.buscar_direto(TABELA_MOTOS_CLIENTES, id_moto_cliente)
        if registro is None or _chassi(registro.get("chassi")) != _chassi(moto.get("chassi")):
            return ""
        com_os = any(int(o.get("id_moto_cliente") or 0) == id_moto_cliente for o in await xano.listar(TABELA_OS))
        outras_vendas = any(int(t.get("id_moto_cliente") or 0) == id_moto_cliente and int(t["id"]) != int(venda["id"])
                            for t in await xano.listar(TABELA))
        if com_os or outras_vendas:
            return (f"A moto {nome} voltou ao estoque, mas continua em Motos dos clientes porque tem ordens de "
                    "serviço ou outras vendas: confira o cadastro.")
        await xano.excluir(TABELA_MOTOS_CLIENTES, id_moto_cliente)
    except Exception:
        return (f"A moto {nome} voltou ao estoque, mas não pôde ser retirada de Motos dos clientes "
                "(falha de conexão): confira o cadastro.")
    return ""


def _juntar(*mensagens: str) -> str:
    return " ".join(m for m in mensagens if m)


async def cancelar_venda(venda_id: int, motivo: str = "", usuario: str = "") -> dict:
    """Devolve {"situacao": "cancelada"|"ja_cancelada"|"erro", "mensagem": str}.
    Marca a venda como cancelada ANTES de devolver o estoque: uma nova
    tentativa nunca devolve em dobro (design D4)."""
    venda_id = int(venda_id)
    async with _travas_venda.setdefault(venda_id, asyncio.Lock()):
        try:
            venda = await _ler_direto(f"{TABELA}/{venda_id}")
        except Exception:
            return {"situacao": "erro", "mensagem": f"Venda nº {venda_id}: falha de conexão, tente de novo."}
        if venda is None:
            return {"situacao": "erro", "mensagem": f"Venda nº {venda_id} não existe."}
        if esta_cancelada(venda):
            return {"situacao": "ja_cancelada", "mensagem": f"Venda nº {venda_id} já estava cancelada."}

        venda_nova = bool((venda.get("status") or "").strip())
        try:
            venda = await _marcar_cancelada(venda, motivo)
        except Exception:
            return {"situacao": "erro", "mensagem": f"Venda nº {venda_id}: falha de conexão, nada foi alterado."}

        # cobrança do Asaas (design D7): só gera aviso, nunca impede o cancelamento
        aviso_cobranca = await pagamentos.cancelar_cobranca_da_venda(venda)

        try:
            itens = await _itens_da_venda(venda_id, venda_nova=venda_nova)
        except Exception:
            return {"situacao": "cancelada", "mensagem": _juntar(
                f"Venda nº {venda_id} cancelada, mas os itens não puderam ser lidos: confira o estoque manualmente.",
                aviso_cobranca)}
        if not itens:
            return {"situacao": "cancelada", "mensagem": _juntar(
                f"Venda nº {venda_id} cancelada. Ela é anterior ao registro de itens: confira o estoque manualmente.",
                aviso_cobranca)}

        avisos_moto = [await _devolver_moto(mid, venda)
                       for mid in sorted({int(i.get(CAMPO_MOTO) or 0) for i in itens} - {0})]
        avisos_moto.append(aviso_cobranca)

        devolucao: dict[int, int] = {}
        for item in itens:
            pid = int(item.get(CAMPO_PRODUTO) or 0)
            if pid:
                devolucao[pid] = devolucao.get(pid, 0) + int(item.get("quantidade") or 0)
        try:
            saldos = await estoque.movimentar(devolucao)
        except Exception:
            nomes = ", ".join(sorted({i.get("descricao") or f"produto {i.get(CAMPO_PRODUTO)}" for i in itens
                                      if int(i.get(CAMPO_PRODUTO) or 0)}))
            return {"situacao": "cancelada", "mensagem": _juntar(
                f"Venda nº {venda_id} cancelada, mas o estoque não pôde ser devolvido ({nomes}): ajuste manualmente.",
                *avisos_moto)}
        await estoque.registrar_historico(devolucao, saldos, "CANCELAMENTO_VENDA", venda_id, usuario)
        return {"situacao": "cancelada", "mensagem": _juntar(*avisos_moto)}


async def cancelar_varias(ids: list[int], motivo: str = "", usuario: str = "") -> list[dict]:
    """Uma de cada vez (não estoura o limite de requisições do Xano Free)."""
    resultados = []
    for venda_id in ids:
        resultado = await cancelar_venda(venda_id, motivo, usuario)
        resultado["id"] = int(venda_id)
        resultados.append(resultado)
    return resultados
