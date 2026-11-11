"""State de Funcionários. Dados vêm do backend Xano."""

from typing import Optional

import reflex as rx

from .. import xano_client as xano
from ..dependencias import em_uso, mensagem_em_uso
from ..constantes import TIPOS_FUNCIONARIO

TABELA = "funcionarios"


class FuncionariosState(rx.State):
    funcionarios: list[dict] = []
    busca: str = ""

    form_id: Optional[int] = None
    nome_funcionario: str = ""
    cargo: str = ""
    tipo: str = TIPOS_FUNCIONARIO[0]
    contato: str = ""
    erro_form: str = ""

    @rx.event
    async def carregar(self):
        registros = await xano.listar(TABELA)
        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [
                r for r in registros
                if termo in (r.get("nome_funcionario") or "").lower()
                or termo in (r.get("cargo") or "").lower()
                or termo in (r.get("tipo") or "").lower()
            ]
        registros = sorted(registros, key=lambda r: (r.get("nome_funcionario") or "").lower())
        self.funcionarios = [
            {
                "id": str(r["id"]),
                "nome_funcionario": r.get("nome_funcionario") or "",
                "cargo": r.get("cargo") or "",
                "tipo": r.get("tipo") or "",
                "contato": r.get("contato") or "—",
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
        self.nome_funcionario = ""
        self.cargo = ""
        self.tipo = TIPOS_FUNCIONARIO[0]
        self.contato = ""
        self.erro_form = ""

    @rx.event
    def editar(self, row: dict):
        self.novo()
        self.form_id = int(row["id"])
        self.nome_funcionario = row["nome_funcionario"]
        self.cargo = row["cargo"]
        self.tipo = row["tipo"] if row["tipo"] in TIPOS_FUNCIONARIO else TIPOS_FUNCIONARIO[0]
        self.contato = "" if row["contato"] == "—" else row["contato"]
        return rx.scroll_to("form-funcionario")

    @rx.event
    async def salvar(self):
        self.erro_form = ""
        nome = " ".join(self.nome_funcionario.split())
        cargo = " ".join(self.cargo.split())
        if not nome or not cargo:
            self.erro_form = "Preencha o nome e o cargo do funcionário."
            return
        if self.tipo not in TIPOS_FUNCIONARIO:
            self.erro_form = "Escolha um tipo válido."
            return
        duplicado = any(
            (r.get("nome_funcionario") or "").strip().lower() == nome.lower() and r["id"] != self.form_id
            for r in await xano.listar(TABELA)
        )
        if duplicado:
            self.erro_form = "Já existe um funcionário com esse nome."
            return

        dados = {
            "nome_funcionario": nome,
            "cargo": cargo,
            "tipo": self.tipo,
            "contato": self.contato.strip() or None,
        }
        if self.form_id is None:
            await xano.criar(TABELA, dados)
            mensagem = f"Funcionário “{nome}” cadastrado."
        else:
            await xano.atualizar(TABELA, self.form_id, dados)
            mensagem = f"Funcionário “{nome}” atualizado."

        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, funcionario_id: str):
        usos = await em_uso(TABELA, int(funcionario_id))
        if usos:
            return rx.toast.error(mensagem_em_uso("este funcionário", usos))
        await xano.excluir(TABELA, int(funcionario_id))
        if self.form_id == int(funcionario_id):
            self.novo()
        await self.carregar()
        return rx.toast.success("Funcionário excluído.")
