"""Testes da venda de moto da loja no Balcão (spec vendas/venda-de-moto-da-loja,
change venda-de-motos-no-balcao). Rodam sem internet: o Xano é simulado em
memória e nada é gravado no Xano real.

    .venv\\Scripts\\python.exe -m unittest discover -s tests -t .
"""

import asyncio
import copy
import unittest
from decimal import Decimal
from unittest import mock

from harley_store import dependencias, email_clientes, estoque, vendas_servico
from harley_store import xano_client as xano
from harley_store.vendas_servico import FalhaVenda
from tests.test_painel import AGORA, item, ms, resumo, venda

CLIENTE = 3


def moto_loja(mid=10, **campos):
    moto = {"id": mid, "marca": "Harley-Davidson", "modelo": "Fat Boy 114", "ano": 2025, "cor": "Preta",
            "placa": "ABC1D23", "chassi": "93HFB114XYZ000001", "renavam": "12345678901", "cilindrada": 1868,
            "quilometragem": 0, "status": "Em estoque", "em_estoque": True, "preco_compra": 100000,
            "preco_venda": 120000, "cliente_id": 0, "data_saida": 0, "foto": {"url": "https://foto"},
            "fotos": None, "created_at": 1}
    moto.update(campos)
    return moto


class XanoFalso:
    """Tabelas em memória com as mesmas funções de xano_client usadas pela venda."""

    def __init__(self, campo_moto=True, **tabelas):
        self.campo_moto = campo_moto  # o Xano já tem itens_transacao.moto_id?
        self.tabelas = {"transacoes": [], "itens_transacao": [], "motos": [], "motos_clientes": [],
                        "clientes": [{"id": CLIENTE, "nome_cliente": "João Pereira", "email": "joao@exemplo.com"}],
                        "ordens_servico": []}
        self.tabelas.update(copy.deepcopy(tabelas))

    def _achar(self, tabela, rid):
        return next((r for r in self.tabelas[tabela] if r["id"] == int(rid)), None)

    async def listar(self, tabela):
        return copy.deepcopy(self.tabelas[tabela])

    async def buscar(self, tabela, rid):
        return copy.deepcopy(self._achar(tabela, rid))

    async def criar(self, tabela, dados):
        dados = dict(dados)
        if tabela == "itens_transacao" and not self.campo_moto:
            dados.pop("moto_id", None)  # campo inexistente: o Xano ignora em silêncio
        registro = {"id": max((r["id"] for r in self.tabelas[tabela]), default=0) + 1, **dados}
        self.tabelas[tabela].append(registro)
        await asyncio.sleep(0)
        return copy.deepcopy(registro)

    async def atualizar(self, tabela, rid, dados):
        registro = {"id": int(rid), **dados}  # o PATCH substitui o registro inteiro
        self.tabelas[tabela] = [r for r in self.tabelas[tabela] if r["id"] != int(rid)] + [registro]
        await asyncio.sleep(0)
        return copy.deepcopy(registro)

    async def excluir(self, tabela, rid):
        self.tabelas[tabela] = [r for r in self.tabelas[tabela] if r["id"] != int(rid)]

    async def ler_direto(self, caminho):
        tabela, _, rid = caminho.partition("/")
        return await (self.buscar(tabela, rid) if rid else self.listar(tabela))

    def instalar(self, teste: unittest.TestCase):
        self.movimentar = mock.AsyncMock(return_value={})
        self.email = mock.Mock(return_value=True)
        for alvo, nome, novo in (
            (xano, "listar", self.listar), (xano, "buscar", self.buscar), (xano, "buscar_direto", self.buscar),
            (xano, "criar", self.criar), (xano, "atualizar", self.atualizar), (xano, "excluir", self.excluir),
            (vendas_servico, "_ler_direto", self.ler_direto), (estoque, "movimentar", self.movimentar),
            (estoque, "registrar_historico", mock.AsyncMock()), (email_clientes, "parabens_compra", self.email),
        ):
            patcher = mock.patch.object(alvo, nome, novo)
            patcher.start()
            teste.addCleanup(patcher.stop)
        return self


ITEM_MOTO = {"id_produto": 0, "id_moto": 10, "descricao": "qualquer", "quantidade": 1, "valor_unitario": 1.0}
CAPACETE = {"id_produto": 7, "descricao": "Capacete", "quantidade": 1, "valor_unitario": 1500}


class TestRegrasDaMoto(unittest.TestCase):
    def test_problema_moto(self):
        self.assertEqual(vendas_servico.problema_moto(moto_loja()), "")
        self.assertEqual(vendas_servico.problema_moto(moto_loja(status="Consignada")), "")
        self.assertIn("já foi vendida", vendas_servico.problema_moto(moto_loja(status="Vendida")))
        self.assertIn("Indisponível", vendas_servico.problema_moto(moto_loja(status="Indisponível")))
        self.assertIn("informe o chassi", vendas_servico.problema_moto(moto_loja(chassi="")))
        self.assertIn("preço de venda", vendas_servico.problema_moto(moto_loja(preco_venda=0)))
        self.assertIn("não existe", vendas_servico.problema_moto(None))

    def test_descricao_traz_os_dados_da_moto(self):
        texto = vendas_servico.descricao_moto(moto_loja(quilometragem=12000))
        for trecho in ("Fat Boy 114", "2025", "Preta", "chassi 93HFB114XYZ000001", "placa ABC1D23",
                       "RENAVAM 12345678901", "1868 cm³", "12.000 km"):
            self.assertIn(trecho, texto)


class TestRegistroDaVendaDeMoto(unittest.IsolatedAsyncioTestCase):
    async def test_venda_com_moto_e_acessorio(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        venda_id, avisos = await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO, CAPACETE])

        transacao = x._achar("transacoes", venda_id)
        self.assertEqual(transacao["valor_total"], 121500)  # preço do cadastro, não o da tela
        item_moto = next(i for i in x.tabelas["itens_transacao"] if i["moto_id"])
        self.assertEqual((item_moto["moto_id"], item_moto["produto_id"], item_moto["valor_unitario"]), (10, 0, 120000))
        self.assertIn("chassi 93HFB114XYZ000001", item_moto["descricao"])

        moto = x._achar("motos", 10)
        self.assertEqual((moto["status"], moto["em_estoque"], moto["cliente_id"]), ("Vendida", False, CLIENTE))
        self.assertEqual(moto["data_saida"], transacao["data_transacao"])
        self.assertEqual(moto["foto"], {"url": "https://foto"})  # registro completo no PATCH

        [moto_cliente] = x.tabelas["motos_clientes"]
        self.assertEqual((moto_cliente["id_cliente"], moto_cliente["placa"], moto_cliente["chassi"]),
                         (CLIENTE, "ABC1D23", "93HFB114XYZ000001"))
        self.assertEqual(transacao["id_moto_cliente"], moto_cliente["id"])
        x.email.assert_called_once()
        self.assertIn("E-mail de parabéns enviado ao cliente.", avisos)
        x.movimentar.assert_called_once_with({7: -1})  # só o capacete mexe no estoque

    async def test_sem_cliente_recusada(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        with self.assertRaises(FalhaVenda) as erro:
            await vendas_servico.registrar_venda("MOTO", 1, 0, 0, [ITEM_MOTO])
        self.assertIn("cliente comprador", str(erro.exception))
        self.assertEqual(x.tabelas["transacoes"], [])

    async def test_duas_motos_recusada(self):
        x = XanoFalso(motos=[moto_loja(), moto_loja(11, chassi="OUTRO1234")]).instalar(self)
        with self.assertRaises(FalhaVenda) as erro:
            await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO, {**ITEM_MOTO, "id_moto": 11}])
        self.assertIn("uma moto da loja por venda", str(erro.exception))

    async def test_moto_ja_vendida_recusada(self):
        x = XanoFalso(motos=[moto_loja(status="Vendida", cliente_id=9)]).instalar(self)
        with self.assertRaises(FalhaVenda) as erro:
            await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO])
        self.assertIn("já foi vendida", str(erro.exception))
        x.movimentar.assert_not_called()

    async def test_disputa_pela_mesma_moto(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        resultados = await asyncio.gather(
            vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO]),
            vendas_servico.registrar_venda("MOTO", 2, CLIENTE, 0, [ITEM_MOTO]),
            return_exceptions=True,
        )
        falhas = [r for r in resultados if isinstance(r, FalhaVenda)]
        self.assertEqual(len(falhas), 1)
        self.assertIn("já foi vendida", str(falhas[0]))
        self.assertEqual(len(x.tabelas["transacoes"]), 1)

    async def test_xano_sem_o_campo_recusa_antes_de_mexer(self):
        antigo = {"id": 1, "transacao_id": 1, "produto_id": 7, "descricao": "Filtro", "quantidade": 1,
                  "valor_unitario": 50}  # registro sem a chave moto_id
        x = XanoFalso(campo_moto=False, motos=[moto_loja()], itens_transacao=[antigo]).instalar(self)
        with self.assertRaises(FalhaVenda) as erro:
            await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO, CAPACETE])
        self.assertIn("aplicar_xano.ps1", str(erro.exception))
        x.movimentar.assert_not_called()
        self.assertEqual(x.tabelas["transacoes"], [])

    async def test_item_gravado_sem_o_campo_desfaz_a_venda(self):
        x = XanoFalso(campo_moto=False, motos=[moto_loja()]).instalar(self)  # tabela de itens vazia
        with self.assertRaises(FalhaVenda) as erro:
            await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO, CAPACETE])
        self.assertIn("aplicar_xano.ps1", str(erro.exception))
        self.assertEqual(x.tabelas["transacoes"][0]["status"], "CANCELADA")
        self.assertEqual(x.movimentar.await_args_list[-1].args[0], {7: 1})  # estoque devolvido
        self.assertEqual(x._achar("motos", 10)["status"], "Em estoque")

    async def test_moto_sem_placa_avisa(self):
        x = XanoFalso(motos=[moto_loja(placa="")]).instalar(self)
        _, avisos = await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO])
        self.assertEqual(x.tabelas["motos_clientes"], [])
        self.assertTrue(any("depois do emplacamento" in a for a in avisos))
        self.assertEqual(x._achar("motos", 10)["status"], "Vendida")

    async def test_cadastro_com_mesmo_chassi_passa_para_o_comprador(self):
        anterior = {"id": 5, "id_cliente": 8, "modelo": "Fat Boy", "placa": "ABC1D23",
                    "chassi": "93HFB114XYZ000001", "imagem": "https://minha-foto"}
        x = XanoFalso(motos=[moto_loja()], motos_clientes=[anterior]).instalar(self)
        venda_id, _ = await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO])
        [registro] = x.tabelas["motos_clientes"]
        self.assertEqual((registro["id"], registro["id_cliente"], registro["imagem"]), (5, CLIENTE, "https://minha-foto"))
        self.assertEqual(x._achar("transacoes", venda_id)["id_moto_cliente"], 5)


class TestCancelamentoDaVendaDeMoto(unittest.IsolatedAsyncioTestCase):
    async def _vender(self, x):
        venda_id, _ = await vendas_servico.registrar_venda("MOTO", 1, CLIENTE, 0, [ITEM_MOTO, CAPACETE])
        return venda_id

    async def test_cancelar_devolve_a_moto(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        venda_id = await self._vender(x)
        resultado = await vendas_servico.cancelar_venda(venda_id, "Cliente desistiu")
        self.assertEqual(resultado, {"situacao": "cancelada", "mensagem": ""})
        moto = x._achar("motos", 10)
        self.assertEqual((moto["status"], moto["em_estoque"], moto["cliente_id"], moto["data_saida"]),
                         ("Em estoque", True, 0, 0))
        self.assertEqual(x.tabelas["motos_clientes"], [])
        self.assertEqual(x.movimentar.await_args_list[-1].args[0], {7: 1})

    async def test_moto_com_ordem_de_servico_mantem_o_cadastro(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        venda_id = await self._vender(x)
        id_moto_cliente = x.tabelas["motos_clientes"][0]["id"]
        x.tabelas["ordens_servico"].append({"id": 1, "id_moto_cliente": id_moto_cliente})
        resultado = await vendas_servico.cancelar_venda(venda_id)
        self.assertIn("continua em Motos dos clientes", resultado["mensagem"])
        self.assertEqual(len(x.tabelas["motos_clientes"]), 1)
        self.assertEqual(x._achar("motos", 10)["status"], "Em estoque")

    async def test_moto_alterada_depois_da_venda_nao_volta(self):
        x = XanoFalso(motos=[moto_loja()]).instalar(self)
        venda_id = await self._vender(x)
        await x.atualizar("motos", 10, {**x._achar("motos", 10), "cliente_id": 99})
        resultado = await vendas_servico.cancelar_venda(venda_id)
        self.assertIn("foi alterada depois da venda", resultado["mensagem"])
        self.assertEqual(x._achar("motos", 10)["status"], "Vendida")


class TestPainelEExclusao(unittest.TestCase):
    def test_moto_do_balcao_conta_uma_vez_em_motos(self):
        hoje = ms(AGORA.year, AGORA.month, AGORA.day, 10)
        item_moto = {**item(1, 0, 1, 120000), "moto_id": 10}
        vendida = {"status": "Vendida", "preco_venda": 120000, "data_saida": hoje}
        r = resumo([venda(1, hoje, "MOTO", 121500)], [item_moto, item(1, 7, 1, 1500)], [vendida])
        self.assertEqual(r["motos_mes"], Decimal("120000"))
        self.assertEqual(r["produtos_mes"], Decimal("1500"))
        self.assertEqual(r["hoje"], Decimal("121500"))

    def test_moto_da_loja_vendida_nao_pode_ser_excluida(self):
        self.assertIn(("itens_transacao", "moto_id", "vendas"), dependencias.REFERENCIAS["motos"])


if __name__ == "__main__":
    unittest.main()
