"""Testes da visão financeira do Painel (motos x produtos). Rodam sem internet,
com dados de exemplo — nada é gravado no Xano.

    .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import datetime
import unittest
from decimal import Decimal

from harley_store.state.dashboard_state import (
    FUSO,
    _moeda,
    lancamentos_faturamento,
    resumo_faturamento,
    valor_estoque_motos,
    valor_estoque_produtos,
)

UTC = datetime.timezone.utc
AGORA = datetime.datetime(2026, 10, 15, 14, 0, tzinfo=FUSO)  # 15/10/2026 14:00 em São Paulo


def ms(ano, mes, dia, hora=12, minuto=0, tz=FUSO) -> int:
    """Data/hora -> epoch em ms, como o Xano grava."""
    return int(datetime.datetime(ano, mes, dia, hora, minuto, tzinfo=tz).timestamp() * 1000)


def venda(vid, data_ms, tipo="BALCAO", total=0, status="ATIVA"):
    return {"id": vid, "tipo_transacao": tipo, "data_transacao": data_ms, "valor_total": total, "status": status}


def item(vid, produto, qtd, unitario):
    return {"transacao_id": vid, "produto_id": produto, "quantidade": qtd, "valor_unitario": unitario}


def resumo(transacoes=(), itens=(), motos=(), ordens=(), itens_os=()):
    return resumo_faturamento(
        lancamentos_faturamento(list(transacoes), list(itens), list(motos), list(ordens), list(itens_os)), AGORA)


def os_(oid, status="CONCLUIDA", concluida_ms=None):
    return {"id": oid, "status": status, "data_abertura": ms(2026, 10, 1), "data_conclusao": concluida_ms}


def item_os(oid, produto, valor):
    return {"id_os": oid, "id_produto": produto, "quantidade": 1, "valor_total_item": valor}


class TestEstoque(unittest.TestCase):
    def test_motos_pelo_custo_e_situacoes(self):
        motos = [
            {"status": "Em estoque", "preco_compra": 100000.10, "preco_venda": 999999},
            {"status": "Reservada", "preco_compra": 50000},
            {"status": "Em manutenção", "preco_compra": 1000},
            {"status": "Em preparação", "preco_compra": 200},
            {"status": "Indisponível", "preco_compra": 30},
            {"status": "Vendida", "preco_compra": 70000},      # fora
            {"status": "Consignada", "preco_compra": 80000},   # fora (moto de terceiro)
            {"status": "Em estoque", "preco_compra": None},    # sem custo preenchido: 0
        ]
        self.assertEqual(valor_estoque_motos(motos), Decimal("151230.10"))

    def test_produtos_sem_estoque_ficam_de_fora(self):
        produtos = [
            {"estoque_qtd": 3, "preco_venda": 0.1},
            {"estoque_qtd": 2, "preco_venda": 349.90},
            {"estoque_qtd": 0, "preco_venda": 1000},   # sem estoque
            {"estoque_qtd": -1, "preco_venda": 1000},  # saldo inválido
        ]
        # Decimal: 3 x 0,10 dá exatamente 0,30 (em float daria 0,30000000000000004)
        self.assertEqual(valor_estoque_produtos(produtos), Decimal("700.10"))

    def test_sem_dados_da_zero(self):
        self.assertEqual(_moeda(valor_estoque_motos([])), "0,00")
        self.assertEqual(_moeda(valor_estoque_produtos([])), "0,00")


class TestFaturamento(unittest.TestCase):
    def test_venda_soma_produtos_e_mao_de_obra(self):
        r = resumo([venda(1, ms(2026, 10, 10), "MOTO", 1290)],
                   [item(1, 7, 2, 500), item(1, 8, 1, 90), item(1, 0, 1, 200)])  # 0 = mão de obra
        self.assertEqual(r["produtos_mes"], Decimal("1290"))
        self.assertEqual(r["motos_mes"], Decimal("0"))  # itens mandam, não o tipo da venda

    def test_balcao_produto_mais_mao_de_obra_no_dia(self):
        # como no print: produto + mão de obra = R$ 228,00 no faturamento de hoje
        r = resumo([venda(1, ms(2026, 10, 15, 10), total=228)], [item(1, 7, 1, 178), item(1, 0, 1, 50)])
        self.assertEqual(r["hoje"], Decimal("228"))

    def test_os_concluida_soma_pecas_e_mao_de_obra_no_dia_da_conclusao(self):
        ordens = [os_(1, concluida_ms=ms(2026, 10, 15, 9))]
        itens_os = [item_os(1, 7, 389.00), item_os(1, 0, 150.00)]  # peça + mão de obra
        r = resumo(ordens=ordens, itens_os=itens_os)
        self.assertEqual(r["hoje"], Decimal("539.00"))
        self.assertEqual(r["produtos_mes"], Decimal("539.00"))

    def test_os_nao_concluida_cancelada_ou_sem_data_nao_conta(self):
        ordens = [
            os_(1, "ABERTA"), os_(2, "EM_ANDAMENTO"),
            os_(3, "CANCELADA", ms(2026, 10, 15)),  # cancelada (data esquecida) não conta
            os_(4, "CONCLUIDA", None),             # concluída antes de existir data_conclusao
        ]
        itens_os = [item_os(i, 0, 100) for i in (1, 2, 3, 4)]
        self.assertEqual(resumo(ordens=ordens, itens_os=itens_os)["total_mes"], Decimal("0"))

    def test_os_concluida_em_outro_dia_conta_no_mes_mas_nao_hoje(self):
        r = resumo(ordens=[os_(1, concluida_ms=ms(2026, 10, 3))], itens_os=[item_os(1, 0, 80)])
        self.assertEqual(r["hoje"], Decimal("0"))
        self.assertEqual(r["produtos_mes"], Decimal("80"))

    def test_desconto_no_preco_unitario_ja_e_liquido(self):
        r = resumo([venda(1, ms(2026, 10, 10), total=269.91)], [item(1, 7, 3, 89.97)])
        self.assertEqual(r["produtos_mes"], Decimal("269.91"))

    def test_venda_cancelada_nao_conta(self):
        r = resumo([venda(1, ms(2026, 10, 10), status="CANCELADA")], [item(1, 7, 1, 100)])
        self.assertEqual(r["total_mes"], Decimal("0"))

    def test_moto_vendida_conta_na_data_de_saida(self):
        motos = [
            {"status": "Vendida", "preco_venda": 105000.50, "data_saida": ms(2026, 10, 15, 0, 0)},
            {"status": "Vendida", "preco_venda": 90000, "data_saida": ms(2026, 9, 30, 0, 0)},  # mês passado
            {"status": "Reservada", "preco_venda": 80000, "data_saida": ms(2026, 10, 1)},     # não vendida
        ]
        r = resumo(motos=motos)
        self.assertEqual(r["motos_mes"], Decimal("105000.50"))
        self.assertEqual(r["hoje"], Decimal("105000.50"))

    def test_os_compra_e_legado(self):
        r = resumo([
            venda(1, ms(2026, 10, 2), "ORDEM_SERVICO", 264.90),  # OS: fora
            venda(2, ms(2026, 10, 2), "COMPRA", 22000),          # compra: fora
            venda(3, ms(2026, 10, 2), "MOTO", 18500),            # legado sem itens: motos
            venda(4, ms(2026, 10, 2), "PECAS", 42.50),           # legado: produtos
            venda(5, ms(2026, 10, 2), "BALCAO", 349.90),         # legado: produtos
        ])
        self.assertEqual(r["motos_mes"], Decimal("18500"))
        self.assertEqual(r["produtos_mes"], Decimal("392.40"))
        self.assertEqual(r["total_mes"], Decimal("18892.40"))

    def test_meia_noite_no_fuso_de_sao_paulo(self):
        # 15/10 00:30 em SP é 15/10 03:30 UTC: é HOJE. 14/10 23:59 em SP é 15/10 02:59 UTC: é ONTEM.
        r = resumo([
            venda(1, ms(2026, 10, 15, 3, 30, tz=UTC)),
            venda(2, ms(2026, 10, 15, 2, 59, tz=UTC)),
        ], [item(1, 7, 1, 10), item(2, 7, 1, 1)])
        self.assertEqual(r["hoje"], Decimal("10"))
        self.assertEqual(r["produtos_mes"], Decimal("11"))

    def test_virada_do_mes_no_fuso(self):
        # 01/10 02:00 UTC ainda é 30/09 23:00 em São Paulo: mês passado
        r = resumo([venda(1, ms(2026, 10, 1, 2, 0, tz=UTC))], [item(1, 7, 1, 500)])
        self.assertEqual(r["total_mes"], Decimal("0"))
        self.assertIn(("set/26", Decimal("500")), r["meses"])

    def test_grafico_doze_meses_soma_motos_e_produtos(self):
        r = resumo([venda(1, ms(2026, 10, 3))], [item(1, 7, 1, 100)],
                   [{"status": "Vendida", "preco_venda": 900, "data_saida": ms(2026, 10, 4)}])
        self.assertEqual(len(r["meses"]), 12)
        self.assertEqual(r["meses"][-1], ("out/26", Decimal("1000")))
        self.assertEqual(r["meses"][0][0], "nov/25")

    def test_sem_vendas_da_zero(self):
        r = resumo()
        self.assertEqual([_moeda(r[k]) for k in ("hoje", "motos_mes", "produtos_mes", "total_mes")],
                         ["0,00"] * 4)

    def test_formato_moeda(self):
        self.assertEqual(_moeda(Decimal("1234.565")), "1.234,57")
        self.assertEqual(_moeda(Decimal("0")), "0,00")


if __name__ == "__main__":
    unittest.main()
