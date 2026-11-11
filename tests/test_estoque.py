"""Testes da movimentação de estoque com um Xano SIMULADO em memória
(não toca no banco real). Cobrem as disputas que causavam perda de baixas.

    .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import asyncio
import copy
import unittest
from unittest import mock

import httpx

from harley_store import estoque
from harley_store import xano_client as xano


class XanoFalso:
    """Tabela `produtos` em memória, com uma pequena espera em cada chamada
    para as operações simultâneas realmente se intercalarem."""

    def __init__(self, produtos: dict[int, dict]):
        self.produtos = produtos
        self.falhar_patch_em: int | None = None

    async def request(self, metodo, url, **kwargs):
        await asyncio.sleep(0.001)
        pid = int(url.rsplit("/", 1)[1])
        req = httpx.Request(metodo, url)
        if pid not in self.produtos:
            return httpx.Response(404, request=req)
        return httpx.Response(200, json=copy.deepcopy(self.produtos[pid]), request=req)

    async def atualizar(self, tabela, pid, dados):
        await asyncio.sleep(0.001)
        if self.falhar_patch_em == pid:
            raise httpx.ConnectError("queda simulada")
        self.produtos[pid] = {"id": pid, **copy.deepcopy(dados)}
        return copy.deepcopy(self.produtos[pid])


def produto(pid, qtd):
    return {"id": pid, "nome_produto": f"P{pid}", "categoria": "Peças", "estoque_qtd": qtd, "preco_venda": 10.0}


class TestEstoque(unittest.IsolatedAsyncioTestCase):
    def usar(self, falso: XanoFalso):
        estoque._travas.clear()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(xano, "_request", falso.request).start()
        mock.patch.object(xano, "atualizar", falso.atualizar).start()

    async def test_baixas_simultaneas_nao_se_perdem(self):
        falso = XanoFalso({1: produto(1, 20)})
        self.usar(falso)
        await asyncio.gather(*(estoque.movimentar({1: -1}) for _ in range(10)))
        self.assertEqual(falso.produtos[1]["estoque_qtd"], 10)

    async def test_disputa_pela_ultima_unidade(self):
        falso = XanoFalso({1: produto(1, 1)})
        self.usar(falso)
        resultados = await asyncio.gather(
            *(estoque.movimentar({1: -1}) for _ in range(5)), return_exceptions=True
        )
        self.assertEqual(sum(isinstance(r, dict) for r in resultados), 1)
        self.assertEqual(sum(isinstance(r, estoque.EstoqueInsuficiente) for r in resultados), 4)
        self.assertEqual(falso.produtos[1]["estoque_qtd"], 0)

    async def test_tudo_ou_nada(self):
        falso = XanoFalso({1: produto(1, 5), 2: produto(2, 0)})
        self.usar(falso)
        with self.assertRaises(estoque.EstoqueInsuficiente):
            await estoque.movimentar({1: -2, 2: -1})
        self.assertEqual(falso.produtos[1]["estoque_qtd"], 5)

    async def test_falha_no_meio_desfaz(self):
        falso = XanoFalso({1: produto(1, 5), 2: produto(2, 5)})
        falso.falhar_patch_em = 2
        self.usar(falso)
        with self.assertRaises(httpx.ConnectError):
            await estoque.movimentar({1: -1, 2: -1})
        self.assertEqual(falso.produtos[1]["estoque_qtd"], 5)

    async def test_produto_inexistente(self):
        self.usar(XanoFalso({}))
        with self.assertRaises(estoque.ProdutoInexistente):
            await estoque.movimentar({99: -1})

    async def test_edicao_do_cadastro_nao_apaga_venda_simultanea(self):
        """Funcionário abre a edição com saldo 10 e digita 12 (+2). Enquanto
        isso, uma venda baixa 3. Resultado certo: 10 - 3 + 2 = 9 (antes: 12)."""
        falso = XanoFalso({1: produto(1, 10)})
        self.usar(falso)
        await estoque.movimentar({1: -3})  # venda durante a edição
        gravado = await estoque.atualizar_produto(1, {"nome_produto": "P1 novo", "estoque_qtd": 999}, +2)
        self.assertEqual(gravado["estoque_qtd"], 9)
        self.assertEqual(falso.produtos[1]["nome_produto"], "P1 novo")

    async def test_edicao_recusa_saldo_negativo(self):
        falso = XanoFalso({1: produto(1, 1)})
        self.usar(falso)
        with self.assertRaises(estoque.EstoqueInsuficiente):
            await estoque.atualizar_produto(1, {}, -5)
        self.assertEqual(falso.produtos[1]["estoque_qtd"], 1)


    async def test_movimentar_devolve_saldos(self):
        self.usar(XanoFalso({1: produto(1, 5), 2: produto(2, 3)}))
        self.assertEqual(await estoque.movimentar({1: -2, 2: +4}), {1: 3, 2: 7})

    async def test_historico_grava_e_nunca_quebra_a_operacao(self):
        gravados = []

        async def criar_ok(tabela, dados):
            gravados.append((tabela, dados))
            return {"id": len(gravados), **dados}

        async def criar_falha(tabela, dados):
            raise httpx.ConnectError("sem conexão")

        with mock.patch.object(xano, "criar", criar_ok):
            await estoque.registrar_historico({1: -2, 2: 0}, {1: 3}, "VENDA", 10, "Ana")
        self.assertEqual(len(gravados), 1)  # variação 0 não gera registro
        self.assertEqual(gravados[0][1], {"produto_id": 1, "quantidade": -2, "saldo_apos": 3,
                                          "origem": "VENDA", "referencia_id": 10, "usuario": "Ana"})
        with mock.patch.object(xano, "criar", criar_falha):
            await estoque.registrar_historico({1: -1}, {1: 2}, "OS", 5)  # não levanta


if __name__ == "__main__":
    unittest.main()
