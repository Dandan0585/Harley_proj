"""
Pagamento das vendas: forma de pagamento, cobrança no Asaas e confirmação
(change pagamento-de-vendas-pelo-asaas, design D2 a D7).

- Funções puras (testadas em tests/test_pagamentos.py): formas, validação,
  dados enviados ao Asaas e tradução da situação da cobrança.
- `gerar_cobranca`: procura ou cria o cliente no Asaas pelo CPF/CNPJ e cria a
  cobrança da venda. Antes de criar, procura uma cobrança com a referência da
  venda, para nunca cobrar duas vezes (ex.: resposta do Asaas perdida).
- `atualizar_pagamentos`: consulta no Asaas as cobranças em aberto e grava a
  venda só quando a situação muda. Na passagem para PAGO, grava primeiro e só
  depois envia o e-mail de confirmação: o e-mail sai uma única vez.
- `cancelar_cobranca_da_venda`: usado pelo cancelamento da venda.

O servidor fica na rede da loja, sem endereço público: por isso a confirmação
é por consulta periódica (`tarefa_periodica`), e não por webhook (design D5).

Tabela no Xano: transacoes + forma_pagamento, situacao_pagamento,
asaas_cobranca_id, link_cobranca e data_pagamento (todos opcionais; vazio =
venda antiga, "Não informado").
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import asaas_client as asaas
from . import email_clientes
from . import xano_client as xano
from .validacao import somente_digitos, validar_cpf_cnpj, validar_email

log = logging.getLogger("harley_store.pagamentos")

try:
    FUSO = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:  # sem tzdata: UTC-3 fixo
    FUSO = datetime.timezone(datetime.timedelta(hours=-3))

TABELA = "transacoes"
TABELA_CLIENTES = "clientes"

# formas de pagamento (código gravado -> texto da tela)
NA_LOJA = "NA_LOJA"
FORMAS = {
    NA_LOJA: "Na loja",
    "BOLETO": "Boleto",
    "CARTAO_CREDITO": "Cartão de crédito",
    "CLIENTE_ESCOLHE": "Cliente escolhe",
}
TIPO_ASAAS = {"BOLETO": "BOLETO", "CARTAO_CREDITO": "CREDIT_CARD", "CLIENTE_ESCOLHE": "UNDEFINED"}

# situação do pagamento da venda
SEM_COBRANCA = "SEM_COBRANCA"
AGUARDANDO = "AGUARDANDO"
PAGO = "PAGO"
VENCIDO = "VENCIDO"
COBRANCA_CANCELADA = "COBRANCA_CANCELADA"
SITUACOES = {
    NA_LOJA: "Na loja",
    SEM_COBRANCA: "Falha na cobrança",
    AGUARDANDO: "Aguardando pagamento",
    PAGO: "Pago",
    VENCIDO: "Vencido",
    COBRANCA_CANCELADA: "Cobrança cancelada",
}
EM_ABERTO = {AGUARDANDO, VENCIDO}  # situações consultadas no Asaas
NAO_INFORMADO = "Não informado"     # venda antiga, sem forma gravada

CAMPOS = ("forma_pagamento", "situacao_pagamento", "asaas_cobranca_id", "link_cobranca", "data_pagamento")
DIAS_VENCIMENTO = 3

_STATUS_PAGO = {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}

# Uma operação por vez em cada venda: cancelamento, nova cobrança e consulta
# do pagamento. vendas_servico usa o mesmo dicionário de travas.
travas_venda: dict[int, asyncio.Lock] = {}


def trava(venda_id: int) -> asyncio.Lock:
    return travas_venda.setdefault(int(venda_id), asyncio.Lock())


# ------------------------------------------------------------ funções puras

def hoje() -> datetime.date:
    return datetime.datetime.now(FUSO).date()


def pelo_asaas(forma: str) -> bool:
    return forma in TIPO_ASAAS


def rotulo_forma(forma: str | None) -> str:
    return FORMAS.get((forma or "").strip(), NAO_INFORMADO)


def rotulo_situacao(situacao: str | None) -> str:
    return SITUACOES.get((situacao or "").strip(), NAO_INFORMADO)


def vencimento_padrao(dia: datetime.date | None = None) -> str:
    return ((dia or hoje()) + datetime.timedelta(days=DIAS_VENCIMENTO)).isoformat()


def problema_forma(forma: str, vencimento: str, dia: datetime.date | None = None,
                   asaas_ligado: bool = True) -> str:
    """Por que a forma/vencimento não serve ("" = serve)."""
    if forma not in FORMAS:
        return f"Forma de pagamento inválida: {forma or '(vazia)'}. Use {', '.join(FORMAS.values())}."
    if not pelo_asaas(forma):
        return ""
    if not asaas_ligado:
        return "A cobrança pelo Asaas não está configurada no servidor: use a forma \"Na loja\"."
    try:
        data = datetime.date.fromisoformat((vencimento or "").strip())
    except ValueError:
        return "Informe a data de vencimento da cobrança."
    if data < (dia or hoje()):
        return "O vencimento não pode ser anterior a hoje: escolha outra data."
    return ""


def problema_cliente(cliente: dict | None) -> str:
    """O cliente serve para cobrança no Asaas? ("" = serve)."""
    if not cliente:
        return "Para cobrar pelo Asaas, escolha o cliente da venda."
    nome = cliente.get("nome_cliente") or "o cliente"
    if validar_cpf_cnpj(cliente.get("cpf_cnpj") or ""):
        return f"O CPF/CNPJ de {nome} é inválido: corrija o cadastro em Clientes."
    email = (cliente.get("email") or "").strip()
    tem_email = bool(email) and not validar_email(email)
    if not tem_email and len(somente_digitos(cliente.get("telefone"))) not in (10, 11):
        return (f"{nome} não tem e-mail nem telefone válidos: complete o cadastro em Clientes "
                "para que ele receba a cobrança.")
    return ""


def _celular(digitos: str) -> bool:
    return len(digitos) == 11 and digitos[2] == "9"


def dados_cliente_asaas(cliente: dict) -> dict:
    """Cadastro do cliente no Asaas, com as notificações (e-mail e SMS) ligadas."""
    dados = {
        "name": (cliente.get("nome_cliente") or "").strip(),
        "cpfCnpj": somente_digitos(cliente.get("cpf_cnpj")),
        "notificationDisabled": False,
        "externalReference": f"cliente-{cliente.get('id')}",
    }
    email = (cliente.get("email") or "").strip()
    if email and not validar_email(email):
        dados["email"] = email
    telefone = somente_digitos(cliente.get("telefone"))
    if _celular(telefone):
        dados["mobilePhone"] = telefone
    elif len(telefone) in (10, 11):
        dados["phone"] = telefone
    if cliente.get("endereco"):
        dados["address"] = str(cliente["endereco"]).strip()[:120]
    return dados


def referencia(venda_id: int) -> str:
    return f"venda-{int(venda_id)}"


def dados_cobranca(venda_id: int, valor: float, cliente_asaas_id: str, forma: str, vencimento: str,
                   loja: str = "Harley Store") -> dict:
    return {
        "customer": cliente_asaas_id,
        "billingType": TIPO_ASAAS[forma],
        "value": round(float(valor), 2),
        "dueDate": vencimento,
        "description": f"Venda nº {int(venda_id)} - {loja}",
        "externalReference": referencia(venda_id),
    }


def situacao_pelo_asaas(cobranca: dict) -> str:
    if cobranca.get("deleted"):
        return COBRANCA_CANCELADA
    status = (cobranca.get("status") or "").upper()
    if status in _STATUS_PAGO:
        return PAGO
    if status == "OVERDUE":
        return VENCIDO
    return AGUARDANDO


def data_pagamento_ms(cobranca: dict) -> int:
    """Data do pagamento informada pelo Asaas (AAAA-MM-DD), ao meio-dia de São Paulo."""
    for campo in ("clientPaymentDate", "paymentDate", "confirmedDate"):
        try:
            dia = datetime.date.fromisoformat(str(cobranca.get(campo) or "")[:10])
        except ValueError:
            continue
        return int(datetime.datetime(dia.year, dia.month, dia.day, 12, tzinfo=FUSO).timestamp() * 1000)
    return xano.datetime_para_epoch_ms()


def data_texto(epoch_ms) -> str:
    if not epoch_ms:
        return ""
    return datetime.datetime.fromtimestamp(float(epoch_ms) / 1000, FUSO).strftime("%d/%m/%Y")


def registro(venda: dict, **mudancas) -> dict:
    """Registro COMPLETO da venda: o PATCH do Xano substitui o registro inteiro."""
    dados = {k: v for k, v in venda.items() if k not in ("id", "created_at")}
    dados.update(mudancas)
    return dados


def _cancelada(venda: dict) -> bool:
    return (venda.get("status") or "").strip().upper() == "CANCELADA"


# ------------------------------------------------------------ Xano preparado?

async def xano_tem_campos() -> bool:
    """O Xano já tem os campos de pagamento em transacoes? (campo inexistente é
    ignorado em silêncio). O cache pode ser de antes da atualização: confere
    direto antes de concluir que não tem."""
    vendas = await xano.listar(TABELA)
    if not vendas or "forma_pagamento" in vendas[0]:
        return True
    resposta = await xano._request("GET", f"{xano.BASE_URL}/{TABELA}")
    resposta.raise_for_status()
    vendas = resposta.json() or []
    return not vendas or "forma_pagamento" in vendas[0]


# ------------------------------------------------------------------ cobrança

async def _cliente_no_asaas(cliente: dict) -> str:
    existente = await asaas.buscar_cliente_por_cpf(somente_digitos(cliente.get("cpf_cnpj")))
    if existente:
        return existente["id"]
    return (await asaas.criar_cliente(dados_cliente_asaas(cliente)))["id"]


async def gerar_cobranca(venda_id: int, vencimento: str = "") -> tuple[bool, str]:
    """Cria (ou reaproveita) a cobrança da venda no Asaas e a liga à venda.
    Nunca levanta exceção: devolve (deu certo, mensagem para o funcionário)."""
    venda_id = int(venda_id)
    async with trava(venda_id):
        try:
            venda = await xano.buscar_direto(TABELA, venda_id)
        except Exception:
            return False, f"Venda nº {venda_id}: falha de conexão com o banco; tente gerar a cobrança de novo."
        if not venda:
            return False, f"Venda nº {venda_id} não existe."
        if _cancelada(venda):
            return False, f"A venda nº {venda_id} está cancelada: não é possível cobrar."
        forma = venda.get("forma_pagamento") or ""
        if not pelo_asaas(forma):
            return False, f"A venda nº {venda_id} não é cobrada pelo Asaas."
        if venda.get("asaas_cobranca_id") and venda.get("situacao_pagamento") != SEM_COBRANCA:
            return True, f"A venda nº {venda_id} já tem cobrança no Asaas."
        cliente = await xano.buscar(TABELA_CLIENTES, int(venda.get("id_cliente") or 0)) \
            if venda.get("id_cliente") else None
        problema = problema_cliente(cliente)
        if problema:
            return False, f"A cobrança da venda nº {venda_id} não foi gerada: {problema}"
        if not vencimento or problema_forma(forma, vencimento):
            vencimento = vencimento_padrao()
        try:
            cobranca = await asaas.buscar_cobranca_por_referencia(referencia(venda_id))
            if not cobranca:
                cobranca = await asaas.criar_cobranca(dados_cobranca(
                    venda_id, float(venda.get("valor_total") or 0), await _cliente_no_asaas(cliente), forma,
                    vencimento, email_clientes.nome_loja()))
        except asaas.FalhaAsaas as erro:
            return False, (f"A cobrança da venda nº {venda_id} não foi gerada: {erro} "
                           "Use \"Gerar cobrança de novo\" na lista de vendas.")
        situacao = situacao_pelo_asaas(cobranca)
        mudancas = {"asaas_cobranca_id": cobranca["id"], "link_cobranca": cobranca.get("invoiceUrl") or "",
                    "situacao_pagamento": situacao}
        if situacao == PAGO:
            mudancas["data_pagamento"] = data_pagamento_ms(cobranca)
        try:
            await xano.atualizar(TABELA, venda_id, registro(venda, **mudancas))
        except Exception:
            return False, (f"A cobrança da venda nº {venda_id} foi criada no Asaas, mas não pôde ser ligada à venda "
                           "(falha de conexão). Use \"Gerar cobrança de novo\": a mesma cobrança será reaproveitada.")
    return True, (f"Cobrança ({rotulo_forma(forma)}, vencimento {data_texto_iso(vencimento)}) gerada no Asaas: "
                  "o cliente recebe o link por e-mail e SMS.")


def data_texto_iso(data_iso: str) -> str:
    partes = (data_iso or "")[:10].split("-")
    return "/".join(reversed(partes)) if len(partes) == 3 else data_iso


# ---------------------------------------------------------- confirmação

async def _enviar_confirmacao(venda: dict) -> None:
    try:
        cliente = await xano.buscar(TABELA_CLIENTES, int(venda.get("id_cliente") or 0))
        if cliente and (cliente.get("email") or "").strip():
            email_clientes.pagamento_confirmado(
                cliente.get("nome_cliente") or "", cliente["email"].strip(), int(venda["id"]),
                float(venda.get("valor_total") or 0), rotulo_forma(venda.get("forma_pagamento")),
                data_texto(venda.get("data_pagamento")))
    except Exception:
        log.exception("e-mail de confirmação da venda %s não pôde ser enviado", venda.get("id"))


async def _atualizar_uma(venda_cache: dict) -> str:
    """Consulta a cobrança de uma venda. Devolve a nova situação, ou "" se não mudou."""
    cobranca = await asaas.buscar_cobranca(venda_cache["asaas_cobranca_id"])
    nova = situacao_pelo_asaas(cobranca)
    if nova == venda_cache.get("situacao_pagamento"):
        return ""  # nada mudou: nenhuma requisição ao Xano
    venda_id = int(venda_cache["id"])
    async with trava(venda_id):
        venda = await xano.buscar_direto(TABELA, venda_id)  # o cache pode estar atrasado
        atual = (venda or {}).get("situacao_pagamento")
        if not venda or _cancelada(venda) or atual not in EM_ABERTO or nova == atual:
            return ""
        mudancas = {"situacao_pagamento": nova}
        if nova == PAGO:
            mudancas["data_pagamento"] = data_pagamento_ms(cobranca)
        gravada = await xano.atualizar(TABELA, venda_id, registro(venda, **mudancas))
    if nova == PAGO:  # só depois de gravar: uma nova consulta não reenvia (design D6)
        await _enviar_confirmacao({**venda, **mudancas, **(gravada or {}), "id": venda_id})
    return nova


async def atualizar_pagamentos() -> dict:
    """Consulta as cobranças em aberto. Devolve {"consultadas", "pagas", "alteradas", "erros"}."""
    resumo = {"consultadas": 0, "pagas": 0, "alteradas": 0, "erros": 0}
    if not asaas.configurado():
        return resumo
    vendas = [v for v in await xano.listar(TABELA)
              if not _cancelada(v) and v.get("situacao_pagamento") in EM_ABERTO and v.get("asaas_cobranca_id")]
    for venda in vendas:
        resumo["consultadas"] += 1
        try:
            nova = await _atualizar_uma(venda)
        except Exception as erro:
            resumo["erros"] += 1
            log.warning("pagamento da venda %s não pôde ser consultado: %r", venda.get("id"), erro)
            continue
        if nova:
            resumo["alteradas"] += 1
            resumo["pagas"] += nova == PAGO
    return resumo


async def tarefa_periodica() -> None:
    """Tarefa de fundo do servidor (registrada em harley_store.py)."""
    await asyncio.sleep(60)  # deixa o cache do Xano aquecer primeiro
    while True:
        try:
            resumo = await atualizar_pagamentos()
            if resumo["alteradas"]:
                log.info("pagamentos atualizados: %s", resumo)
        except asyncio.CancelledError:
            raise
        except Exception as erro:
            log.warning("consulta dos pagamentos falhou: %r", erro)
        await asyncio.sleep(asaas.intervalo_minutos() * 60)


# ---------------------------------------------------------- cancelamento

async def cancelar_cobranca_da_venda(venda: dict) -> str:
    """Chamado por vendas_servico.cancelar_venda, DENTRO da trava da venda e
    depois de marcá-la como cancelada. Devolve o aviso ("" = nada a avisar)."""
    forma = venda.get("forma_pagamento") or ""
    situacao = venda.get("situacao_pagamento") or ""
    venda_id = int(venda["id"])
    if not pelo_asaas(forma) or situacao == COBRANCA_CANCELADA:
        return ""
    if situacao == PAGO:
        return (f"A venda nº {venda_id} já estava paga: faça o estorno do pagamento no painel do Asaas.")
    if not asaas.configurado():
        return f"Cancele a cobrança da venda nº {venda_id} no painel do Asaas (integração desligada no servidor)."
    try:
        cobranca_id = venda.get("asaas_cobranca_id") or ""
        if not cobranca_id:  # SEM_COBRANCA: a cobrança pode ter sido criada e a resposta perdida
            achada = await asaas.buscar_cobranca_por_referencia(referencia(venda_id))
            if not achada:
                return ""
            cobranca_id = achada["id"]
        cobranca = await asaas.buscar_cobranca(cobranca_id)
        if situacao_pelo_asaas(cobranca) == PAGO:
            return (f"A cobrança da venda nº {venda_id} já tinha sido paga no Asaas: "
                    "faça o estorno no painel do Asaas.")
        await asaas.cancelar_cobranca(cobranca_id)
    except asaas.FalhaAsaas:
        return (f"A cobrança da venda nº {venda_id} não pôde ser cancelada no Asaas: "
                "cancele-a no painel do Asaas.")
    try:
        await xano.atualizar(TABELA, venda_id, registro(venda, situacao_pagamento=COBRANCA_CANCELADA,
                                                        asaas_cobranca_id=cobranca_id))
    except Exception:
        pass  # a cobrança já foi cancelada no Asaas; a situação se corrige na tela pela venda cancelada
    return f"Cobrança da venda nº {venda_id} cancelada no Asaas."
