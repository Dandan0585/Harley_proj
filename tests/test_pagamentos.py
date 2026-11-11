"""Testes do pagamento das vendas pelo Asaas (spec vendas/pagamento-da-venda,
change pagamento-de-vendas-pelo-asaas). Rodam sem internet: o Asaas e o Xano
são simulados em memória; nada é enviado ao Asaas nem gravado no Xano real.

    .venv\\Scripts\\python.exe -m unittest discover -s tests -t .
"""

import datetime
import json
import os
import unittest
from unittest import mock

import httpx

from harley_store import asaas_client, email_clientes, pagamentos_servico as pag, vendas_servico
from harley_store.vendas_servico import FalhaVenda
from tests.test_venda_de_moto import CAPACETE, XanoFalso

HOJE = datetime.date(2026, 11, 11)
CPF = "529.982.247-25"  # CPF válido de exemplo
CLIENTE = {"id": 3, "nome_cliente": "João Pereira", "cpf_cnpj": CPF, "email": "joao@exemplo.com",
           "telefone": "(11) 98765-4321", "endereco": ""}
AMANHA = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
ENV = {"ASAAS_API_KEY": "chave-de-teste", "ASAAS_AMBIENTE": "sandbox"}


class AsaasFalso:
    """Clientes e cobranças em memória, com as funções de asaas_client."""

    def __init__(self):
        self.clientes: list[dict] = []
        self.cobrancas: list[dict] = []
        self.falhar_criacao = False
        self.falhar_tudo = False

    def _conferir(self):
        if self.falhar_tudo:
            raise asaas_client.FalhaAsaas("Não foi possível conectar ao Asaas (falha de conexão).")

    async def buscar_cliente_por_cpf(self, cpf):
        self._conferir()
        return next((c for c in self.clientes if c["cpfCnpj"] == cpf), None)

    async def criar_cliente(self, dados):
        self._conferir()
        cliente = {"id": f"cus_{len(self.clientes) + 1}", **dados}
        self.clientes.append(cliente)
        return cliente

    async def criar_cobranca(self, dados):
        self._conferir()
        if self.falhar_criacao:
            raise asaas_client.FalhaAsaas("Não foi possível conectar ao Asaas (falha de conexão).")
        numero = len(self.cobrancas) + 1
        cobranca = {"id": f"pay_{numero}", "status": "PENDING", "invoiceUrl": f"https://asaas/i/{numero}", **dados}
        self.cobrancas.append(cobranca)
        return dict(cobranca)

    def _achar(self, cid):
        return next(c for c in self.cobrancas if c["id"] == cid)

    async def buscar_cobranca(self, cid):
        self._conferir()
        return dict(self._achar(cid))

    async def buscar_cobranca_por_referencia(self, ref):
        self._conferir()
        return next((dict(c) for c in self.cobrancas if c["externalReference"] == ref and not c.get("deleted")), None)

    async def cancelar_cobranca(self, cid):
        self._conferir()
        self._achar(cid)["deleted"] = True
        return {"deleted": True, "id": cid}

    def instalar(self, teste):
        for nome in ("buscar_cliente_por_cpf", "criar_cliente", "criar_cobranca", "buscar_cobranca",
                     "buscar_cobranca_por_referencia", "cancelar_cobranca"):
            patcher = mock.patch.object(asaas_client, nome, getattr(self, nome))
            patcher.start()
            teste.addCleanup(patcher.stop)
        patcher = mock.patch.dict(os.environ, ENV)
        patcher.start()
        teste.addCleanup(patcher.stop)
        return self


# ---------------------------------------------------------------- funções puras

class TestRegrasPuras(unittest.TestCase):
    def test_forma_e_vencimento(self):
        self.assertIn("inválida", pag.problema_forma("CHEQUE", "", HOJE))
        self.assertEqual(pag.problema_forma("NA_LOJA", "", HOJE, asaas_ligado=False), "")
        self.assertIn("não está configurada", pag.problema_forma("BOLETO", "2026-11-14", HOJE, asaas_ligado=False))
        self.assertIn("vencimento", pag.problema_forma("BOLETO", "", HOJE))
        self.assertIn("anterior a hoje", pag.problema_forma("BOLETO", "2026-11-10", HOJE))
        self.assertEqual(pag.problema_forma("CARTAO_CREDITO", "2026-11-11", HOJE), "")
        self.assertEqual(pag.vencimento_padrao(HOJE), "2026-11-14")

    def test_cliente_para_cobranca(self):
        self.assertIn("escolha o cliente", pag.problema_cliente(None))
        self.assertIn("CPF/CNPJ", pag.problema_cliente({**CLIENTE, "cpf_cnpj": "111.111.111-11"}))
        self.assertIn("complete o cadastro", pag.problema_cliente({**CLIENTE, "email": "", "telefone": ""}))
        self.assertEqual(pag.problema_cliente({**CLIENTE, "email": ""}), "")  # só celular: recebe por SMS
        self.assertEqual(pag.problema_cliente({**CLIENTE, "telefone": ""}), "")

    def test_dados_do_cliente_no_asaas(self):
        dados = pag.dados_cliente_asaas(CLIENTE)
        self.assertEqual((dados["name"], dados["cpfCnpj"], dados["email"], dados["mobilePhone"]),
                         ("João Pereira", "52998224725", "joao@exemplo.com", "11987654321"))
        self.assertIs(dados["notificationDisabled"], False)  # e-mail e SMS do Asaas ligados
        fixo = pag.dados_cliente_asaas({**CLIENTE, "telefone": "(11) 3333-4444"})
        self.assertEqual(fixo["phone"], "1133334444")
        self.assertNotIn("mobilePhone", fixo)

    def test_dados_da_cobranca(self):
        for forma, tipo in (("BOLETO", "BOLETO"), ("CARTAO_CREDITO", "CREDIT_CARD"),
                            ("CLIENTE_ESCOLHE", "UNDEFINED")):
            dados = pag.dados_cobranca(120, 213.0, "cus_1", forma, "2026-11-14")
            self.assertEqual((dados["billingType"], dados["value"], dados["dueDate"], dados["externalReference"]),
                             (tipo, 213.0, "2026-11-14", "venda-120"))
            self.assertIn("Venda nº 120", dados["description"])

    def test_situacao_pelo_asaas(self):
        for status, esperado in (("PENDING", pag.AGUARDANDO), ("RECEIVED", pag.PAGO), ("CONFIRMED", pag.PAGO),
                                 ("RECEIVED_IN_CASH", pag.PAGO), ("OVERDUE", pag.VENCIDO)):
            self.assertEqual(pag.situacao_pelo_asaas({"status": status}), esperado)
        self.assertEqual(pag.situacao_pelo_asaas({"status": "PENDING", "deleted": True}), pag.COBRANCA_CANCELADA)

    def test_data_do_pagamento(self):
        ms = pag.data_pagamento_ms({"paymentDate": "2026-11-12"})
        self.assertEqual(pag.data_texto(ms), "12/11/2026")

    def test_rotulos_de_venda_antiga(self):
        self.assertEqual(pag.rotulo_forma(None), "Não informado")
        self.assertEqual(pag.rotulo_situacao(""), "Não informado")
        self.assertEqual(pag.rotulo_situacao("PAGO"), "Pago")


# ------------------------------------------------------------- registro da venda

class Base(unittest.IsolatedAsyncioTestCase):
    def preparar(self, **tabelas):
        tabelas.setdefault("clientes", [dict(CLIENTE)])
        self.x = XanoFalso(**tabelas).instalar(self)
        self.a = AsaasFalso().instalar(self)
        self.email = mock.Mock(return_value=True)
        patcher = mock.patch.object(email_clientes, "pagamento_confirmado", self.email)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def vender(self, forma="BOLETO", cliente=3, vencimento=AMANHA):
        return await vendas_servico.registrar_venda("BALCAO", 1, cliente, 0, [dict(CAPACETE)], "",
                                                    forma, vencimento)

    def venda(self, vid):
        return self.x._achar("transacoes", vid)


class TestRegistroComPagamento(Base):
    async def test_venda_na_loja_nao_usa_o_asaas(self):
        self.preparar()
        vid, _ = await self.vender("NA_LOJA", cliente=0, vencimento="")
        self.assertEqual((self.venda(vid)["forma_pagamento"], self.venda(vid)["situacao_pagamento"]),
                         ("NA_LOJA", "NA_LOJA"))
        self.assertEqual(self.a.cobrancas, [])

    async def test_venda_com_boleto_gera_cobranca(self):
        self.preparar()
        vid, avisos = await self.vender("BOLETO")
        venda = self.venda(vid)
        self.assertEqual((venda["situacao_pagamento"], venda["asaas_cobranca_id"], venda["link_cobranca"]),
                         ("AGUARDANDO", "pay_1", "https://asaas/i/1"))
        [cobranca] = self.a.cobrancas
        self.assertEqual((cobranca["billingType"], cobranca["value"], cobranca["dueDate"], cobranca["customer"]),
                         ("BOLETO", 1500.0, AMANHA, "cus_1"))
        self.assertEqual(self.a.clientes[0]["cpfCnpj"], "52998224725")
        self.assertTrue(any("e-mail e SMS" in a for a in avisos))
        self.assertEqual(venda["valor_total"], 1500)  # o restante da venda não muda

    async def test_segunda_venda_reaproveita_o_cliente_no_asaas(self):
        self.preparar()
        await self.vender("BOLETO")
        await self.vender("CARTAO_CREDITO")
        self.assertEqual(len(self.a.clientes), 1)
        self.assertEqual([c["billingType"] for c in self.a.cobrancas], ["BOLETO", "CREDIT_CARD"])

    async def test_forma_invalida_nao_altera_nada(self):
        self.preparar()
        with self.assertRaises(FalhaVenda) as erro:
            await self.vender("CHEQUE")
        self.assertIn("inválida", str(erro.exception))
        self.x.movimentar.assert_not_called()
        self.assertEqual(self.x.tabelas["transacoes"], [])

    async def test_boleto_sem_cliente_nao_altera_nada(self):
        self.preparar()
        with self.assertRaises(FalhaVenda) as erro:
            await self.vender("BOLETO", cliente=0)
        self.assertIn("escolha o cliente", str(erro.exception))
        self.x.movimentar.assert_not_called()

    async def test_vencimento_no_passado(self):
        self.preparar()
        with self.assertRaises(FalhaVenda):
            await self.vender("BOLETO", vencimento="2020-01-01")
        self.x.movimentar.assert_not_called()

    async def test_sem_chave_do_asaas_so_na_loja(self):
        self.preparar()
        with mock.patch.dict(os.environ, {"ASAAS_API_KEY": ""}):
            with self.assertRaises(FalhaVenda) as erro:
                await self.vender("BOLETO")
            self.assertIn("Na loja", str(erro.exception))
            vid, _ = await self.vender("NA_LOJA", vencimento="")
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "NA_LOJA")

    async def test_falha_no_asaas_mantem_a_venda_e_permite_nova_tentativa(self):
        self.preparar()
        self.a.falhar_criacao = True
        vid, avisos = await self.vender("BOLETO")
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "SEM_COBRANCA")
        self.assertTrue(any("Gerar cobrança de novo" in a for a in avisos))
        self.x.movimentar.assert_called_once()  # o estoque continua baixado

        self.a.falhar_criacao = False
        ok, _ = await pag.gerar_cobranca(vid)
        self.assertTrue(ok)
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "AGUARDANDO")
        self.assertEqual(len(self.a.cobrancas), 1)

    async def test_nova_tentativa_reaproveita_cobranca_ja_criada(self):
        self.preparar()
        self.a.falhar_criacao = True
        vid, _ = await self.vender("BOLETO")
        # a cobrança foi criada no Asaas, mas a resposta se perdeu
        self.a.falhar_criacao = False
        await self.a.criar_cobranca(pag.dados_cobranca(vid, 1500, "cus_1", "BOLETO", AMANHA))
        ok, _ = await pag.gerar_cobranca(vid)
        self.assertTrue(ok)
        self.assertEqual(len(self.a.cobrancas), 1)
        self.assertEqual(self.venda(vid)["asaas_cobranca_id"], "pay_1")


# ------------------------------------------------------------ confirmação

class TestConfirmacao(Base):
    async def test_boleto_pago_envia_um_unico_email(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        self.a.cobrancas[0].update(status="RECEIVED", paymentDate="2026-11-12")

        resumo = await pag.atualizar_pagamentos()
        self.assertEqual((resumo["pagas"], resumo["alteradas"]), (1, 1))
        venda = self.venda(vid)
        self.assertEqual(venda["situacao_pagamento"], "PAGO")
        self.assertEqual(pag.data_texto(venda["data_pagamento"]), "12/11/2026")
        self.email.assert_called_once()
        nome, email, venda_id, valor, forma, data = self.email.call_args.args
        self.assertEqual((email, venda_id, valor, forma, data), ("joao@exemplo.com", vid, 1500.0, "Boleto",
                                                                 "12/11/2026"))

        await pag.atualizar_pagamentos()  # consulta repetida
        self.email.assert_called_once()

    async def test_vencido_e_depois_pago(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        self.a.cobrancas[0]["status"] = "OVERDUE"
        await pag.atualizar_pagamentos()
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "VENCIDO")
        self.email.assert_not_called()
        self.a.cobrancas[0]["status"] = "RECEIVED"
        await pag.atualizar_pagamentos()
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "PAGO")
        self.email.assert_called_once()

    async def test_consulta_sem_mudanca_nao_grava(self):
        self.preparar()
        await self.vender("BOLETO")
        with mock.patch.object(vendas_servico.xano, "atualizar") as atualizar:
            resumo = await pag.atualizar_pagamentos()
        atualizar.assert_not_called()
        self.assertEqual((resumo["consultadas"], resumo["alteradas"]), (1, 0))

    async def test_falha_ao_gravar_nao_envia_email(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        self.a.cobrancas[0]["status"] = "RECEIVED"
        with mock.patch.object(vendas_servico.xano, "atualizar", mock.AsyncMock(side_effect=RuntimeError)):
            resumo = await pag.atualizar_pagamentos()
        self.assertEqual(resumo["erros"], 1)
        self.email.assert_not_called()
        await pag.atualizar_pagamentos()  # na próxima consulta dá certo
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "PAGO")
        self.email.assert_called_once()

    async def test_cliente_sem_email_nao_recebe(self):
        self.preparar(clientes=[{**CLIENTE, "email": ""}])
        vid, _ = await self.vender("BOLETO")
        self.a.cobrancas[0]["status"] = "RECEIVED"
        await pag.atualizar_pagamentos()
        self.assertEqual(self.venda(vid)["situacao_pagamento"], "PAGO")
        self.email.assert_not_called()


# ------------------------------------------------------------ cancelamento

class TestCancelamento(Base):
    async def test_cancelar_boleto_em_aberto(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        resultado = await vendas_servico.cancelar_venda(vid, "Cliente desistiu")
        self.assertEqual(resultado["situacao"], "cancelada")
        self.assertTrue(self.a.cobrancas[0].get("deleted"))
        venda = self.venda(vid)
        self.assertEqual((venda["status"], venda["situacao_pagamento"]), ("CANCELADA", "COBRANCA_CANCELADA"))
        self.assertEqual(venda["forma_pagamento"], "BOLETO")  # PATCH completo: os dados do pagamento ficam

    async def test_cancelar_venda_paga_avisa_estorno(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        self.a.cobrancas[0]["status"] = "RECEIVED"
        await pag.atualizar_pagamentos()
        resultado = await vendas_servico.cancelar_venda(vid)
        self.assertIn("estorno", resultado["mensagem"])
        venda = self.venda(vid)
        self.assertEqual((venda["status"], venda["situacao_pagamento"], venda["asaas_cobranca_id"]),
                         ("CANCELADA", "PAGO", "pay_1"))
        self.assertFalse(self.a.cobrancas[0].get("deleted"))

    async def test_asaas_fora_do_ar_no_cancelamento(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        self.a.falhar_tudo = True
        resultado = await vendas_servico.cancelar_venda(vid)
        self.assertEqual(resultado["situacao"], "cancelada")
        self.assertIn("painel do Asaas", resultado["mensagem"])
        self.assertEqual(self.venda(vid)["status"], "CANCELADA")

    async def test_venda_cancelada_nao_e_consultada(self):
        self.preparar()
        vid, _ = await self.vender("BOLETO")
        await vendas_servico.cancelar_venda(vid)
        resumo = await pag.atualizar_pagamentos()
        self.assertEqual(resumo["consultadas"], 0)


# ------------------------------------------------------------ e-mail

class TestEmailDeConfirmacao(unittest.TestCase):
    def test_conteudo_e_nome_como_texto(self):
        with mock.patch.object(email_clientes, "_agendar", return_value=True) as agendar:
            email_clientes.pagamento_confirmado("<b>Ana</b> Souza", "ana@exemplo.com", 120, 213.0, "Boleto",
                                                "12/11/2026")
        _, _, assunto, corpo_html, corpo_texto = agendar.call_args.args
        self.assertEqual(assunto, "Pagamento confirmado - venda nº 120")
        for trecho in ("nº 120", "R$ 213,00", "Boleto", "12/11/2026"):
            self.assertIn(trecho, corpo_html)
            self.assertIn(trecho, corpo_texto)
        self.assertIn("&lt;b&gt;Ana&lt;/b&gt;", corpo_html)
        self.assertNotIn("<b>Ana</b>", corpo_html)


# ------------------------------------------------------------ cliente HTTP

class TestClienteAsaas(unittest.IsolatedAsyncioTestCase):
    def usar_transporte(self, tratar):
        real = httpx.AsyncClient
        patcher = mock.patch.object(asaas_client.httpx, "AsyncClient",
                                    lambda **kw: real(transport=httpx.MockTransport(tratar), **kw))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.dict(os.environ, ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_cabecalhos_e_endereco_do_sandbox(self):
        pedidos = []

        def tratar(pedido):
            pedidos.append(pedido)
            return httpx.Response(200, json={"id": "pay_1", "status": "PENDING"})

        self.usar_transporte(tratar)
        cobranca = await asaas_client.criar_cobranca({"value": 10})
        self.assertEqual(cobranca["id"], "pay_1")
        [pedido] = pedidos
        self.assertEqual(str(pedido.url), "https://api-sandbox.asaas.com/v3/payments")
        self.assertEqual(pedido.headers["access_token"], "chave-de-teste")
        self.assertEqual(pedido.headers["User-Agent"], "HarleyStore")
        self.assertEqual(json.loads(pedido.content), {"value": 10})

    async def test_erro_do_asaas_em_portugues_sem_a_chave(self):
        self.usar_transporte(lambda p: httpx.Response(
            400, json={"errors": [{"code": "invalid_cpfCnpj", "description": "CPF/CNPJ informado é inválido."}]}))
        with self.assertRaises(asaas_client.FalhaAsaas) as erro:
            await asaas_client.criar_cliente({})
        self.assertIn("CPF/CNPJ informado é inválido", str(erro.exception))
        self.assertNotIn("chave-de-teste", str(erro.exception))

    async def test_chave_recusada(self):
        self.usar_transporte(lambda p: httpx.Response(401, json={}))
        with self.assertRaises(asaas_client.FalhaAsaas) as erro:
            await asaas_client.saldo()
        self.assertIn("ASAAS_API_KEY", str(erro.exception))

    async def test_sem_configuracao(self):
        with mock.patch.dict(os.environ, {"ASAAS_API_KEY": ""}):
            self.assertFalse(asaas_client.configurado())
            with self.assertRaises(asaas_client.FalhaAsaas):
                await asaas_client.saldo()
        with mock.patch.dict(os.environ, {"ASAAS_API_KEY": "x", "ASAAS_AMBIENTE": "producao"}):
            self.assertFalse(asaas_client.configurado())  # só o Sandbox nesta versão


if __name__ == "__main__":
    unittest.main()
