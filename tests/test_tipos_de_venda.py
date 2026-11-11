"""Testes dos tipos de venda (spec vendas/venda-com-itens, requisito "Tipos de
venda"). Rodam sem internet: o estoque é simulado e nada é gravado no Xano.

    .venv\\Scripts\\python.exe -m unittest discover -s tests -t .
"""

import unittest
from decimal import Decimal
from unittest import mock

from harley_store import estoque, vendas_servico
from harley_store.constantes import TIPOS_VENDA
from tests.test_painel import AGORA, item, ms, resumo, venda

ITEM = [{"id_produto": 7, "descricao": "Filtro", "quantidade": 1, "valor_unitario": 50}]


class TestTiposOferecidos(unittest.TestCase):
    def test_tela_oferece_so_balcao_pecas_e_moto(self):
        self.assertEqual(TIPOS_VENDA, ["BALCAO", "PECAS", "MOTO"])


class TestRecusaNoServidor(unittest.IsolatedAsyncioTestCase):
    async def test_tipo_invalido_recusado_sem_mexer_no_estoque(self):
        for tipo in ("COMPRA", "ORDEM_SERVICO", "", "qualquer"):
            with self.subTest(tipo=tipo), \
                    mock.patch.object(estoque, "movimentar", mock.AsyncMock()) as movimentar:
                with self.assertRaises(vendas_servico.FalhaVenda) as erro:
                    await vendas_servico.registrar_venda(tipo, 1, 0, 0, ITEM)
                self.assertIn("Tipo de venda inválido", str(erro.exception))
                movimentar.assert_not_called()

    async def test_tipos_validos_passam_da_conferencia(self):
        # O estoque simulado recusa a baixa: chegar até ele prova que o tipo foi aceito.
        recusa = mock.AsyncMock(side_effect=estoque.EstoqueInsuficiente(["Filtro"]))
        for tipo in TIPOS_VENDA:
            with self.subTest(tipo=tipo), mock.patch.object(estoque, "movimentar", recusa):
                with self.assertRaises(vendas_servico.FalhaVenda) as erro:
                    await vendas_servico.registrar_venda(tipo, 1, 0, 0, ITEM)
                self.assertIn("Estoque insuficiente", str(erro.exception))


class TestFaturamentoPorTipo(unittest.TestCase):
    def test_venda_moto_com_item_conta_em_produtos_hoje(self):
        r = resumo([venda(1, ms(AGORA.year, AGORA.month, AGORA.day, 10), "MOTO", 300)], [item(1, 0, 1, 300)])
        self.assertEqual(r["hoje"], Decimal("300"))
        self.assertEqual(r["produtos_mes"], Decimal("300"))
        self.assertEqual(r["motos_mes"], Decimal("0"))

    def test_vendas_antigas_compra_e_os_continuam_fora(self):
        r = resumo([venda(1, ms(2026, 10, 2), "ORDEM_SERVICO", 264.90),
                    venda(2, ms(2026, 10, 2), "COMPRA", 22000)])
        self.assertEqual(r["total_mes"], Decimal("0"))


if __name__ == "__main__":
    unittest.main()
