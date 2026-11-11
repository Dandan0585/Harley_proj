"""Recuperação do cliente HTTP depois de queda de rede (sem internet: Xano simulado).

    .venv\\Scripts\\python.exe -m unittest discover -s tests -t . -v
"""

import unittest
from unittest import mock

import httpx

from harley_store import xano_client as xano


class ClienteFalso:
    """Cada instância é um "pool de conexões"; a primeira fica quebrada."""
    criados: list["ClienteFalso"] = []

    def __init__(self, timeout=None):
        self.quebrado = not ClienteFalso.criados
        self.is_closed = False
        ClienteFalso.criados.append(self)

    async def request(self, metodo, url, **kwargs):
        if self.quebrado:
            raise httpx.ConnectError("All connection attempts failed")
        return httpx.Response(200, json=[], request=httpx.Request(metodo, url))

    async def aclose(self):
        self.is_closed = True


class TestRecuperacaoDeConexao(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        ClienteFalso.criados = []
        xano._cliente = None
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(xano.httpx, "AsyncClient", ClienteFalso).start()
        mock.patch.object(xano, "_ESPERA_BASE_SEGUNDOS", 0).start()

    async def test_leitura_troca_o_cliente_quebrado_e_funciona(self):
        resposta = await xano._request("GET", "https://exemplo/api/produtos", autenticar=False)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(ClienteFalso.criados), 2)

    async def test_gravacao_nao_repete_mas_a_proxima_chamada_funciona(self):
        with self.assertRaises(httpx.ConnectError):
            await xano._request("POST", "https://exemplo/api/produtos", autenticar=False, json={})
        resposta = await xano._request("POST", "https://exemplo/api/produtos", autenticar=False, json={})
        self.assertEqual(resposta.status_code, 200)


if __name__ == "__main__":
    unittest.main()
