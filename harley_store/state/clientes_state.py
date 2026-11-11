"""State de Clientes. Dados vêm do backend Xano.

CPF/CNPJ é validado (dígitos verificadores) e gravado sempre formatado
(000.000.000-00 / 00.000.000/0000-00): assim a duplicidade é conferida pelos
números, não pela forma como foi digitado.
"""

from typing import Optional

import reflex as rx

from .. import email_clientes
from .. import xano_client as xano
from ..dependencias import em_uso, mensagem_em_uso
from ..validacao import (
    formatar_cpf_cnpj,
    formatar_telefone,
    somente_digitos,
    validar_cpf_cnpj,
    validar_email,
    validar_telefone,
)

TABELA = "clientes"


class ClientesState(rx.State):
    clientes: list[dict] = []
    busca: str = ""

    form_id: Optional[int] = None
    nome_cliente: str = ""
    cpf_cnpj: str = ""
    telefone: str = ""
    email: str = ""
    endereco: str = ""
    erro_form: str = ""

    @rx.event
    async def carregar(self):
        registros = await xano.listar(TABELA)
        if self.busca.strip():
            termo = self.busca.strip().lower()
            digitos = somente_digitos(termo)
            registros = [
                r for r in registros
                if termo in (r.get("nome_cliente") or "").lower()
                or termo in (r.get("email") or "").lower()
                or (digitos and (digitos in somente_digitos(r.get("cpf_cnpj"))
                                 or digitos in somente_digitos(r.get("telefone"))))
            ]
        registros = sorted(registros, key=lambda r: (r.get("nome_cliente") or "").lower())
        self.clientes = [
            {
                "id": str(r["id"]),
                "nome_cliente": r.get("nome_cliente") or "",
                "cpf_cnpj": r.get("cpf_cnpj") or "",
                "telefone": r.get("telefone") or "—",
                "email": r.get("email") or "—",
                "endereco": r.get("endereco") or "—",
            }
            for r in registros
        ]

    @rx.event
    async def definir_busca(self, valor: str):
        self.busca = valor
        await self.carregar()

    @rx.event
    def novo(self):
        self.form_id = None
        self.nome_cliente = ""
        self.cpf_cnpj = ""
        self.telefone = ""
        self.email = ""
        self.endereco = ""
        self.erro_form = ""

    @rx.event
    def editar(self, row: dict):
        self.novo()
        self.form_id = int(row["id"])
        self.nome_cliente = row["nome_cliente"]
        self.cpf_cnpj = row["cpf_cnpj"]
        self.telefone = "" if row["telefone"] == "—" else row["telefone"]
        self.email = "" if row["email"] == "—" else row["email"]
        self.endereco = "" if row["endereco"] == "—" else row["endereco"]
        return rx.scroll_to("form-cliente")

    @rx.event
    async def salvar(self):
        self.erro_form = ""
        nome = " ".join(self.nome_cliente.split())
        if not nome or not self.cpf_cnpj.strip():
            self.erro_form = "Preencha o nome e o CPF/CNPJ do cliente."
            return
        if len(nome) < 3:
            self.erro_form = "Informe o nome completo do cliente."
            return
        erro = (validar_cpf_cnpj(self.cpf_cnpj) or validar_telefone(self.telefone)
                or validar_email(self.email))
        if erro:
            self.erro_form = erro
            return
        doc = formatar_cpf_cnpj(self.cpf_cnpj)

        duplicado = next(
            (r for r in await xano.listar(TABELA)
             if somente_digitos(r.get("cpf_cnpj")) == somente_digitos(doc) and r["id"] != self.form_id),
            None,
        )
        if duplicado:
            self.erro_form = f"Já existe um cliente com esse CPF/CNPJ: {duplicado.get('nome_cliente')}."
            return

        dados = {
            "nome_cliente": nome,
            "cpf_cnpj": doc,
            "telefone": formatar_telefone(self.telefone) or None,
            "email": self.email.strip().lower() or None,
            "endereco": self.endereco.strip() or None,
        }
        if self.form_id is None:
            await xano.criar(TABELA, dados)
            mensagem = f"Cliente “{nome}” cadastrado."
            if dados["email"] and email_clientes.boas_vindas(nome, dados["email"]):
                mensagem += " E-mail de boas-vindas enviado."
        else:
            await xano.atualizar(TABELA, self.form_id, dados)
            mensagem = f"Cliente “{nome}” atualizado."

        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, cliente_id: str):
        usos = await em_uso(TABELA, int(cliente_id))
        if usos:
            return rx.toast.error(mensagem_em_uso("este cliente", usos))
        await xano.excluir(TABELA, int(cliente_id))
        if self.form_id == int(cliente_id):
            self.novo()
        await self.carregar()
        return rx.toast.success("Cliente excluído.")
