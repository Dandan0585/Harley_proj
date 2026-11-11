"""
State do Painel (dashboard).

A lista `atividades_recentes` reproduz em Python a ideia da view SQL
original `vw_resumo_operacoes` (que juntava Transacoes + Entrada de
Mercadoria num só extrato) — um bom exemplo de como combinar duas
tabelas num só relatório dentro de um State, caso você queira montar
outros relatórios parecidos no futuro.

Dados vêm do backend Xano.

Visão financeira (motos x produtos) — regras aprovadas pelo dono da loja:

- Estoque de Motos: soma do PREÇO DE COMPRA (custo) das motos nas situações
  de STATUS_ESTOQUE_MOTOS. Fora: Vendida e Consignada (moto de terceiro).
- Estoque de Produtos: quantidade x preço de venda (a tabela não tem preço
  de custo nem campo "ativo"), só produtos com estoque > 0.
- Faturamento (só vendas não canceladas; o valor dos itens já é líquido,
  pois o desconto é dado no preço unitário):
    * Motos: motos marcadas "Vendida", pelo preço de venda, na data de saída
      (vendidas em Produtos > Motos ou no Balcão) + vendas antigas do tipo MOTO
      sem itens. O item de venda que é moto da loja (moto_id) não conta de novo.
    * Produtos e serviços: itens das vendas (produtos do estoque e itens
      avulsos, como mão de obra); OS CONCLUIDAS, com peças + mão de obra, na
      data de conclusão (`data_conclusao`); vendas antigas sem itens dos tipos
      PECAS e BALCAO.
    * Fora: vendas do tipo COMPRA (compra não é faturamento) e do tipo
      ORDEM_SERVICO (a OS conta pela própria conclusão; somar as duas contaria
      em dobro). OS concluída antes de existir `data_conclusao` não tem dia
      definido e não entra.
- Dia e mês no fuso America/Sao_Paulo (o Xano grava data em UTC, epoch ms).
- Dinheiro em Decimal; float só no fim, para o gráfico.
As funções puras abaixo fazem as contas (testadas em tests/test_painel.py).
"""

import asyncio
import datetime
import logging
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import reflex as rx

from .. import xano_client as xano
from ..vendas_servico import CAMPO_MOTO, CAMPO_VENDA, esta_cancelada
from .produtos_state import LIMITE_ESTOQUE_BAIXO  # uma só regra de "estoque baixo"

log = logging.getLogger("harley_store.painel")

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

try:
    FUSO = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:
    # sem o pacote tzdata (requirements.txt): o Brasil não tem horário de verão desde 2019
    log.warning("pacote tzdata ausente: usando UTC-3 fixo para America/Sao_Paulo")
    FUSO = datetime.timezone(datetime.timedelta(hours=-3), "America/Sao_Paulo")

STATUS_ESTOQUE_MOTOS = {"Em estoque", "Em preparação", "Em manutenção", "Reservada", "Indisponível"}
TIPOS_LEGADO_MOTOS = {"MOTO"}
TIPOS_LEGADO_PRODUTOS = {"PECAS", "BALCAO"}
TIPOS_FORA_DO_FATURAMENTO = {"ORDEM_SERVICO", "COMPRA"}
CENTAVO = Decimal("0.01")


def _moeda(valor) -> str:
    """1234.5 -> "1.234,50" (formato brasileiro). Aceita Decimal ou número."""
    valor = Decimal(str(valor or 0)).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _dec(valor) -> Decimal:
    """Valor vindo do Xano (número ou None) -> Decimal exato do que foi gravado."""
    return Decimal(str(valor)) if valor not in (None, "") else Decimal(0)


def data_local(epoch_ms) -> datetime.datetime | None:
    """Epoch em ms (UTC, como o Xano grava) -> data/hora em America/Sao_Paulo."""
    if not epoch_ms:
        return None
    return datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=FUSO)


def valor_estoque_motos(motos: list[dict]) -> Decimal:
    return sum((_dec(m.get("preco_compra")) for m in motos
                if (m.get("status") or "Em estoque") in STATUS_ESTOQUE_MOTOS), Decimal(0))


def valor_estoque_produtos(produtos: list[dict]) -> Decimal:
    return sum((int(p.get("estoque_qtd") or 0) * _dec(p.get("preco_venda")) for p in produtos
                if int(p.get("estoque_qtd") or 0) > 0), Decimal(0))


def lancamentos_faturamento(transacoes: list[dict], itens: list[dict], motos: list[dict],
                            ordens: list[dict] = (), itens_os: list[dict] = ()):
    """[(data local, "motos" | "produtos", valor Decimal)] conforme as regras do topo.
    "produtos" = produtos e serviços (mão de obra)."""
    itens_por_venda: dict[int, list[dict]] = {}
    for item in itens:
        itens_por_venda.setdefault(int(item.get(CAMPO_VENDA) or 0), []).append(item)

    lancamentos = []
    for t in transacoes:
        tipo = (t.get("tipo_transacao") or "").strip().upper()
        data = data_local(t.get("data_transacao"))
        if esta_cancelada(t) or tipo in TIPOS_FORA_DO_FATURAMENTO or data is None:
            continue
        itens_da_venda = itens_por_venda.get(int(t["id"]))
        if itens_da_venda:
            for item in itens_da_venda:  # produto do estoque ou avulso (mão de obra)
                if int(item.get(CAMPO_MOTO) or 0):
                    continue  # moto da loja: conta pela própria moto (Vendida), logo abaixo
                lancamentos.append((data, "produtos",
                                    int(item.get("quantidade") or 0) * _dec(item.get("valor_unitario"))))
        elif tipo in TIPOS_LEGADO_MOTOS:
            lancamentos.append((data, "motos", _dec(t.get("valor_total"))))
        elif tipo in TIPOS_LEGADO_PRODUTOS:
            lancamentos.append((data, "produtos", _dec(t.get("valor_total"))))

    for m in motos:
        data = data_local(m.get("data_saida"))
        if m.get("status") == "Vendida" and data is not None:
            lancamentos.append((data, "motos", _dec(m.get("preco_venda"))))

    valor_por_os: dict[int, Decimal] = {}
    for item in itens_os:  # valor_total_item já é o total do item (peça ou mão de obra)
        os_id = int(item.get("id_os") or 0)
        valor_por_os[os_id] = valor_por_os.get(os_id, Decimal(0)) + _dec(item.get("valor_total_item"))
    for o in ordens:
        data = data_local(o.get("data_conclusao"))
        if (o.get("status") or "") == "CONCLUIDA" and data is not None:
            lancamentos.append((data, "produtos", valor_por_os.get(int(o["id"]), Decimal(0))))
    return lancamentos


def resumo_faturamento(lancamentos, agora: datetime.datetime) -> dict:
    """Totais do dia (00:00 a 23:59) e do mês corrente (dia 1, 00:00, até o fim de
    hoje), em America/Sao_Paulo, e a série dos últimos 12 meses (motos + produtos)."""
    agora = agora.astimezone(FUSO)
    inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_dia = inicio_dia + datetime.timedelta(days=1)
    inicio_mes = inicio_dia.replace(day=1)

    def soma(inicio, categoria=None):
        return sum((v for d, c, v in lancamentos
                    if inicio <= d < fim_dia and (categoria is None or c == categoria)), Decimal(0))

    por_mes: dict[tuple[int, int], Decimal] = {}
    for i in range(11, -1, -1):
        ano, mes = divmod(agora.year * 12 + agora.month - 1 - i, 12)
        por_mes[(ano, mes + 1)] = Decimal(0)
    for d, _categoria, v in lancamentos:
        if (d.year, d.month) in por_mes and d < fim_dia:
            por_mes[(d.year, d.month)] += v

    return {
        "hoje": soma(inicio_dia),
        "motos_mes": soma(inicio_mes, "motos"),
        "produtos_mes": soma(inicio_mes, "produtos"),
        "total_mes": soma(inicio_mes),
        "meses": [(f"{MESES[m - 1]}/{a % 100:02d}", v) for (a, m), v in por_mes.items()],
    }


class DashboardState(rx.State):
    total_produtos: int = 0
    produtos_estoque_baixo: int = 0
    total_clientes: int = 0
    os_em_aberto: int = 0
    # "—" até a primeira leitura: se o Xano falhar, o painel não mostra um R$ 0,00 falso
    faturamento_hoje: str = "—"
    faturamento_motos_mes: str = "—"
    faturamento_produtos_mes: str = "—"
    faturamento_total_mes: str = "—"
    atividades_recentes: list[dict] = []

    # Motos da loja (tabela `motos`)
    motos_em_estoque: int = 0
    valor_estoque_motos: str = "—"     # preço de compra (custo)
    valor_estoque_produtos: str = "—"  # quantidade x preço de venda
    motos_vendidas_mes: int = 0

    # Gráfico: faturamento (motos + produtos) por mês, últimos 12 meses ({"mes": "set/26", "valor": 1234.5})
    faturamento_12_meses: list[dict] = []

    @rx.event
    async def carregar(self):
        hoje = datetime.date.today()
        inicio_mes = datetime.datetime.combine(hoje.replace(day=1), datetime.time.min)

        # As 10 tabelas são buscadas em paralelo: em sequência o painel levava
        # ~12 s para abrir (cada chamada ao Xano Free leva 1–2 s). Se o Xano
        # devolver 429 (limite por minuto), `_request` já refaz a chamada.
        (
            produtos, lista_clientes, motos, ordens, transacoes,
            lista_funcionarios, lista_fornecedores, entradas, itens_venda, itens_os,
        ) = await asyncio.gather(
            *(
                xano.listar(tabela)
                for tabela in (
                    "produtos", "clientes", "motos", "ordens_servico", "transacoes",
                    "funcionarios", "fornecedores", "entrada_mercadoria", "itens_transacao",
                    "itens_ordem_servico",
                )
            )
        )

        self.total_produtos = len(produtos)
        self.produtos_estoque_baixo = sum(1 for p in produtos if (p.get("estoque_qtd") or 0) <= LIMITE_ESTOQUE_BAIXO)

        self.total_clientes = len(lista_clientes)

        em_estoque = [m for m in motos if m.get("em_estoque")]
        self.motos_em_estoque = len(em_estoque)
        self.valor_estoque_motos = _moeda(valor_estoque_motos(motos))
        self.valor_estoque_produtos = _moeda(valor_estoque_produtos(produtos))
        self.motos_vendidas_mes = sum(
            1
            for m in motos
            if m.get("status") == "Vendida"
            and m.get("data_saida")
            and xano.epoch_ms_para_datetime(m["data_saida"]) >= inicio_mes
        )

        self.os_em_aberto = sum(1 for o in ordens if o.get("status") in ("ABERTA", "EM_ANDAMENTO"))

        # Faturamento: motos x produtos (regras no topo do arquivo)
        resumo = resumo_faturamento(
            lancamentos_faturamento(transacoes, itens_venda, motos, ordens, itens_os), datetime.datetime.now(FUSO)
        )
        self.faturamento_hoje = _moeda(resumo["hoje"])
        self.faturamento_motos_mes = _moeda(resumo["motos_mes"])
        self.faturamento_produtos_mes = _moeda(resumo["produtos_mes"])
        self.faturamento_total_mes = _moeda(resumo["total_mes"])
        self.faturamento_12_meses = [
            {"mes": rotulo, "valor": float(v.quantize(CENTAVO, rounding=ROUND_HALF_UP))}
            for rotulo, v in resumo["meses"]
        ]

        transacoes_com_data = [
            (t, xano.epoch_ms_para_datetime(t["data_transacao"])) for t in transacoes
        ]

        funcionarios = {f["id"]: f["nome_funcionario"] for f in lista_funcionarios}
        clientes = {c["id"]: c["nome_cliente"] for c in lista_clientes}
        fornecedores = {f["id"]: f["nome_fornecedor"] for f in lista_fornecedores}

        atividades = [
            {
                "origem": "Venda (cancelada)" if esta_cancelada(t) else "Venda",
                "tipo": t["tipo_transacao"],
                "quem": clientes.get(t.get("id_cliente"), funcionarios.get(t["id_funcionario"], "—")),
                "data": d,
                "valor": t["valor_total"],
            }
            for t, d in transacoes_com_data
        ] + [
            {
                "origem": "Compra",
                "tipo": "ENTRADA ESTOQUE",
                "quem": fornecedores.get(e["id_fornecedor"], "—"),
                "data": xano.epoch_ms_para_datetime(e["data_entrada"]),
                "valor": e["valor_total"],
            }
            for e in entradas
        ]
        atividades.sort(key=lambda a: a["data"], reverse=True)

        self.atividades_recentes = [
            {
                "origem": a["origem"],
                "tipo": a["tipo"],
                "quem": a["quem"],
                "data": a["data"].strftime("%d/%m/%Y %H:%M"),
                "valor": _moeda(a["valor"]),
            }
            for a in atividades[:12]
        ]
