"""
State de Fornecedores — este arquivo é o template mais simples de CRUD
do projeto. Para criar um cadastro novo parecido (uma tabela sem
relacionamento com outras), copie este arquivo e ajuste os campos.

Os dados vêm do backend Xano (workspace HARLEY) via `xano_client`, não
mais do SQLite local — ver `xano_client.py` para detalhes da API.
Padrão das telas de cadastro: validação no servidor (`validacao.py`), erro
mostrado no formulário (`erro_form`), sucesso em aviso (toast) e exclusão
bloqueada quando o registro está em uso (`dependencias.py`).
"""

from typing import Optional

import reflex as rx

from .. import xano_client as xano
from ..dependencias import em_uso, mensagem_em_uso
from ..validacao import formatar_cpf_cnpj, somente_digitos, validar_cnpj

TABELA = "fornecedores"


class FornecedoresState(rx.State):
    fornecedores: list[dict] = []
    busca: str = ""

    # campos do formulário (sempre como string; convertidos ao salvar)
    form_id: Optional[int] = None
    nome_fornecedor: str = ""
    cnpj: str = ""
    contato: str = ""
    erro_form: str = ""

    @rx.event
    async def carregar(self):
        registros = await xano.listar(TABELA)
        if self.busca.strip():
            termo = self.busca.strip().lower()
            digitos = somente_digitos(termo)
            registros = [
                r for r in registros
                if termo in (r.get("nome_fornecedor") or "").lower()
                or termo in (r.get("contato") or "").lower()
                or (digitos and digitos in somente_digitos(r.get("cnpj")))
            ]
        registros = sorted(registros, key=lambda r: (r.get("nome_fornecedor") or "").lower())
        self.fornecedores = [
            {
                "id": str(r["id"]),
                "nome_fornecedor": r.get("nome_fornecedor") or "",
                "cnpj": r.get("cnpj") or "",
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
        self.nome_fornecedor = ""
        self.cnpj = ""
        self.contato = ""
        self.erro_form = ""

    @rx.event
    def editar(self, row: dict):
        self.novo()
        self.form_id = int(row["id"])
        self.nome_fornecedor = row["nome_fornecedor"]
        self.cnpj = row["cnpj"]
        self.contato = "" if row["contato"] == "—" else row["contato"]
        return rx.scroll_to("form-fornecedor")

    @rx.event
    async def salvar(self):
        self.erro_form = ""
        nome = " ".join(self.nome_fornecedor.split())
        if not nome or not self.cnpj.strip():
            self.erro_form = "Preencha o nome e o CNPJ do fornecedor."
            return
        erro = validar_cnpj(self.cnpj)
        if erro:
            self.erro_form = erro
            return
        cnpj = formatar_cpf_cnpj(self.cnpj)

        duplicado = next(
            (r for r in await xano.listar(TABELA)
             if somente_digitos(r.get("cnpj")) == somente_digitos(cnpj) and r["id"] != self.form_id),
            None,
        )
        if duplicado:
            self.erro_form = f"Já existe um fornecedor com esse CNPJ: {duplicado.get('nome_fornecedor')}."
            return

        dados = {"nome_fornecedor": nome, "cnpj": cnpj, "contato": self.contato.strip() or None}
        if self.form_id is None:
            await xano.criar(TABELA, dados)
            mensagem = f"Fornecedor “{nome}” cadastrado."
        else:
            await xano.atualizar(TABELA, self.form_id, dados)
            mensagem = f"Fornecedor “{nome}” atualizado."

        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, fornecedor_id: str):
        usos = await em_uso(TABELA, int(fornecedor_id))
        if usos:
            return rx.toast.error(mensagem_em_uso("este fornecedor", usos))
        await xano.excluir(TABELA, int(fornecedor_id))
        if self.form_id == int(fornecedor_id):
            self.novo()
        await self.carregar()
        return rx.toast.success("Fornecedor excluído.")
