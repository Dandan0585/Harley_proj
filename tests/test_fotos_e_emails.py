"""Testes das fotos oficiais, da descrição de compras e dos e-mails (rodam sem internet).

    .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import asyncio
import os
import unittest
from pathlib import Path
from unittest import mock

from harley_store import email_clientes
from harley_store.fotos_oficiais import cilindrada_oficial, foto_oficial
from harley_store.state.compras_state import descricao_dos_itens

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class TestFotosOficiais(unittest.TestCase):
    def test_modelos_da_loja_tem_foto(self):
        for modelo in ["Harley-Davidson Iron 883", "Fat Boy 114", "heritage classic", "Sportster S",
                       "Pan America 1250 Special", "Street Glide Special", "Road Glide Limited",
                       "Low Rider S", "Breakout 117", "Nightster Special"]:
            foto = foto_oficial(modelo)
            self.assertTrue(foto, modelo)
            self.assertTrue((ASSETS / foto.lstrip("/")).exists(), foto)

    def test_modelo_parecido_nao_ganha_foto_errada(self):
        # nada de foto "inventada": modelo não reconhecido fica sem foto
        for modelo in ["Low Rider ST", "Street Glide", "Fat Bob 114", "Sportster", ""]:
            self.assertEqual(foto_oficial(modelo), "", modelo)

    def test_cilindrada(self):
        self.assertEqual(cilindrada_oficial("Iron 883"), 883)
        self.assertEqual(cilindrada_oficial("Breakout 117"), 1923)
        self.assertEqual(cilindrada_oficial("Modelo qualquer"), 0)


class TestDescricaoCompra(unittest.TestCase):
    def test_descricao_dos_itens(self):
        self.assertEqual(descricao_dos_itens([("Pneu Traseiro", 2), ("Óleo 10W30", 10)]),
                         "2x Pneu Traseiro; 10x Óleo 10W30")
        self.assertEqual(descricao_dos_itens([]), "")


class TestEmails(unittest.TestCase):
    def test_sem_configuracao_nao_envia(self):
        with mock.patch.dict(os.environ, {"SENDGRID_API_KEY": "", "SENDGRID_REMETENTE": ""}):
            self.assertFalse(email_clientes.boas_vindas("Ana Souza", "ana@exemplo.com"))

    def test_envia_para_o_sendgrid(self):
        enviado = {}

        class Resposta:
            status_code = 202
            text = ""

        async def post(_self, url, json, headers):
            enviado.update(url=url, json=json, headers=headers)
            return Resposta()

        async def cenario():
            with mock.patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.teste", "SENDGRID_REMETENTE": "loja@exemplo.com"}), \
                    mock.patch("httpx.AsyncClient.post", post):
                self.assertTrue(email_clientes.parabens_compra("<b>Ana</b> Souza", "ana@exemplo.com",
                                                               "Harley-Davidson Fat Boy 114"))
                await asyncio.gather(*email_clientes._tarefas)

        asyncio.run(cenario())
        self.assertEqual(enviado["url"], "https://api.sendgrid.com/v3/mail/send")
        self.assertEqual(enviado["headers"]["Authorization"], "Bearer SG.teste")
        self.assertEqual(enviado["json"]["personalizations"][0]["to"][0]["email"], "ana@exemplo.com")
        self.assertIn("Fat Boy 114", enviado["json"]["subject"])
        corpo_html = enviado["json"]["content"][1]["value"]
        self.assertNotIn("<b>Ana", corpo_html)  # nome do cliente é escapado no HTML


class Resposta202:
    status_code = 202
    text = ""


def _capturar_envio(destino: dict):
    async def post(_self, url, json, headers):
        destino.update(url=url, json=json, headers=headers)
        return Resposta202()
    return post


CONFIGURADO = {"SENDGRID_API_KEY": "SG.teste", "SENDGRID_REMETENTE": "loja@exemplo.com"}
SEM_CONFIGURACAO = {"SENDGRID_API_KEY": "", "SENDGRID_REMETENTE": ""}


class TestBoasVindasConta(unittest.TestCase):
    """Spec plataforma/boas-vindas-da-conta."""

    def test_email_da_conta_sem_senha_e_com_nome_escapado(self):
        enviado = {}

        async def cenario():
            with mock.patch.dict(os.environ, CONFIGURADO), mock.patch("httpx.AsyncClient.post", _capturar_envio(enviado)):
                self.assertTrue(email_clientes.boas_vindas_conta("<i>Ana</i> Souza", "ana@exemplo.com"))
                await asyncio.gather(*email_clientes._tarefas)

        asyncio.run(cenario())
        self.assertEqual(enviado["json"]["personalizations"][0]["to"][0]["email"], "ana@exemplo.com")
        texto, corpo_html = (c["value"] for c in enviado["json"]["content"])
        self.assertNotIn("<i>Ana", corpo_html)
        self.assertIn("uma conta de acesso", corpo_html)
        self.assertNotIn("é cliente", corpo_html)
        self.assertIn("ana@exemplo.com", texto)
        self.assertIn("pessoalmente", texto)

    def test_email_de_cliente_mantem_o_rodape(self):
        self.assertIn("porque é cliente da", email_clientes._modelo_html("t", ["p"]))


class _UsuariosFalso:
    """Faz o papel do UsuariosState em UsuariosState.salvar (sem o Reflex)."""

    def __init__(self):
        self.novo_nome_completo, self.novo_email = "Ana Souza", "Ana@Exemplo.com"
        self.nova_senha = self.nova_confirmar_senha = "SenhaForte123"
        self.erro = ""

    async def _token_admin(self):
        return "token-admin"

    def limpar_formulario(self):
        pass

    async def carregar(self):
        pass


class TestCriarContaEnviaBoasVindas(unittest.IsolatedAsyncioTestCase):
    async def _salvar(self, criar_usuario):
        from harley_store.state import usuarios_state

        estado = _UsuariosFalso()
        envio = mock.MagicMock(side_effect=lambda nome, email: email_clientes.configurado())
        with mock.patch.object(usuarios_state.admin, "criar_usuario", criar_usuario), \
                mock.patch.object(usuarios_state.email_clientes, "boas_vindas_conta", envio), \
                mock.patch.object(usuarios_state, "_senha_valida", lambda _s: True):
            retorno = await usuarios_state.UsuariosState.salvar.fn(estado)
        return estado, envio, retorno

    async def test_conta_criada_envia_ao_email_da_conta(self):
        with mock.patch.dict(os.environ, CONFIGURADO):
            _estado, envio, retorno = await self._salvar(mock.AsyncMock())
        envio.assert_called_once_with("Ana Souza", "ana@exemplo.com")
        self.assertIn("E-mail de boas-vindas enviado.", str(retorno))

    async def test_conta_recusada_nao_envia(self):
        from harley_store import xano_admin_client

        recusa = mock.AsyncMock(side_effect=xano_admin_client.ErroAdmin("already exists"))
        with mock.patch.dict(os.environ, CONFIGURADO):
            estado, envio, _ = await self._salvar(recusa)
        envio.assert_not_called()
        self.assertEqual(estado.erro, "Esse email já está cadastrado.")

    async def test_sem_configuracao_cria_a_conta_sem_avisar_envio(self):
        criar = mock.AsyncMock()
        with mock.patch.dict(os.environ, SEM_CONFIGURACAO):
            _estado, _envio, retorno = await self._salvar(criar)
        criar.assert_awaited_once()
        self.assertNotIn("E-mail de boas-vindas", str(retorno))


if __name__ == "__main__":
    unittest.main()
