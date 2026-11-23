"""Telas só de administrador e tela inicial por perfil (sem o Xano real).

    .venv\\Scripts\\python.exe -m unittest discover -s tests -t . -v
"""

import unittest
from types import SimpleNamespace

from harley_store.sessao import ExigeSessaoMiddleware
from harley_store.state.auth_state import SESSAO_OK, AuthState, tela_inicial_do_perfil
from harley_store.state.clientes_state import ClientesState
from harley_store.state.dashboard_state import DashboardState
from harley_store.state.vendas_state import VendasState


class AuthFalso:
    def __init__(self, perfil: str):
        self.eh_admin = perfil == "admin"
        self.auth_user_id = 7
        self.conferencias = 0

    async def validar_sessao(self):
        self.conferencias += 1
        return SESSAO_OK


class EstadoFalso:
    def __init__(self, auth: AuthFalso):
        self._auth = auth

    async def get_state(self, classe):
        assert classe is AuthState
        return self._auth


def evento(state_cls, handler: str = "carregar"):
    return SimpleNamespace(name=f"{state_cls.get_full_name()}.{handler}", token="t", router_data={})


class TestTelasSoAdmin(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.middleware = ExigeSessaoMiddleware([VendasState], so_admin=[ClientesState, DashboardState])

    async def processar(self, perfil: str, state_cls, handler: str = "carregar"):
        return await self.middleware.preprocess(None, EstadoFalso(AuthFalso(perfil)), evento(state_cls, handler))

    async def test_funcionario_e_recusado_nas_telas_de_admin(self):
        for state_cls, handler in ((DashboardState, "carregar"), (ClientesState, "excluir"), (ClientesState, "salvar")):
            with self.subTest(handler=handler):
                resposta = await self.processar("member", state_cls, handler)
                self.assertIsNotNone(resposta)
                self.assertTrue(resposta.final)
                self.assertEqual(resposta.events, [])

    async def test_perfil_nao_conferido_e_recusado(self):
        self.assertIsNotNone(await self.processar("", DashboardState))

    async def test_admin_e_aceito(self):
        self.assertIsNone(await self.processar("admin", DashboardState))
        self.assertIsNone(await self.processar("admin", ClientesState, "excluir"))

    async def test_funcionario_segue_nas_demais_telas(self):
        self.assertIsNone(await self.processar("member", VendasState))

    async def test_tela_de_admin_tambem_exige_sessao(self):
        auth = AuthFalso("admin")
        await self.middleware.preprocess(None, EstadoFalso(auth), evento(DashboardState))
        self.assertEqual(auth.conferencias, 1)


class TestTelaInicial(unittest.TestCase):
    def test_por_perfil(self):
        self.assertEqual(tela_inicial_do_perfil("admin"), "/painel")
        self.assertEqual(tela_inicial_do_perfil("member"), "/vendas")
        self.assertEqual(tela_inicial_do_perfil(""), "/vendas")


if __name__ == "__main__":
    unittest.main()
