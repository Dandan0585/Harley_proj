"""
State de Usuários do sistema (contas de login na tabela `user` do Xano) —
diferente de Funcionários (que é cadastro de RH).

Só administradores (perfil "admin") usam esta tela: criar contas, trocar
e-mail, definir uma nova senha, mudar o perfil e excluir contas. A regra é
aplicada no Xano (toda chamada leva o token de quem está logado e o Xano
confere o perfil); a tela só evita mostrar o que a pessoa não pode usar.
"""

from __future__ import annotations

import logging

import reflex as rx

from .. import email_clientes
from .. import xano_admin_client as admin
from ..validacao import validar_email
from .auth_state import AuthState, _MENSAGEM_SENHA_INVALIDA, _senha_valida

log = logging.getLogger("harley_store.usuarios")

PERFIS = {"admin": "Administrador", "member": "Funcionário"}


class UsuariosState(rx.State):
    usuarios: list[dict] = []
    sem_permissao: bool = False

    novo_nome_completo: str = ""
    novo_email: str = ""
    nova_senha: str = ""
    nova_confirmar_senha: str = ""
    erro: str = ""

    # diálogo "definir nova senha"
    senha_usuario_id: str = ""
    senha_usuario_nome: str = ""
    senha_nova: str = ""
    senha_confirmar: str = ""
    senha_erro: str = ""

    async def _token_admin(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.auth_token if auth.eh_admin else ""

    @rx.event
    async def carregar(self):
        token = await self._token_admin()
        if not token:
            self.sem_permissao, self.usuarios = True, []
            return
        try:
            registros = await admin.listar_usuarios(token)
        except admin.SemPermissao:
            self.sem_permissao, self.usuarios = True, []
            return
        self.sem_permissao = False
        self.usuarios = [
            {
                "id": str(r["id"]),
                "nome": r.get("name") or "",
                "email": r.get("email") or "",
                "perfil": PERFIS.get(r.get("role") or "member", "Funcionário"),
            }
            for r in sorted(registros, key=lambda r: (r.get("name") or "").lower())
        ]

    @rx.event
    def limpar_formulario(self):
        self.novo_nome_completo = ""
        self.novo_email = ""
        self.nova_senha = ""
        self.nova_confirmar_senha = ""
        self.erro = ""

    @rx.event
    async def salvar(self):
        nome_completo = " ".join(self.novo_nome_completo.split())
        email = self.novo_email.strip().lower()
        senha = self.nova_senha
        if not nome_completo or not email or not senha:
            self.erro = "Preencha todos os campos."
            return
        if validar_email(email):
            self.erro = validar_email(email)
            return
        if not _senha_valida(senha):
            self.erro = _MENSAGEM_SENHA_INVALIDA
            return
        if senha != self.nova_confirmar_senha:
            self.erro = "As senhas não coincidem."
            return
        token = await self._token_admin()
        try:
            await admin.criar_usuario(token, nome_completo, email, senha)
        except admin.SemPermissao:
            self.erro = "Só administradores podem criar contas."
            return
        except admin.ErroAdmin as erro:
            self.erro = ("Esse email já está cadastrado." if "already exists" in str(erro).lower()
                         else "Não foi possível criar a conta. Verifique os dados e tente novamente.")
            return
        log.info("conta criada por admin: %s", email)
        mensagem = f"Conta de {nome_completo} criada (perfil Funcionário)."
        # Só depois da conta criada; a senha nunca vai no e-mail.
        if email_clientes.boas_vindas_conta(nome_completo, email):
            mensagem += " E-mail de boas-vindas enviado."
        self.limpar_formulario()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def atualizar_email(self, usuario_id: str, novo_email: str):
        novo_email = novo_email.strip().lower()
        atual = next((u for u in self.usuarios if u["id"] == usuario_id), None)
        if atual and atual["email"] == novo_email:
            return
        if not novo_email or validar_email(novo_email):
            return rx.toast.error(validar_email(novo_email) or "Informe o novo e-mail.")
        if any(u["email"].lower() == novo_email and u["id"] != usuario_id for u in self.usuarios):
            return rx.toast.error("Esse e-mail já é usado por outra conta.")
        await admin.atualizar_email(await self._token_admin(), int(usuario_id), novo_email)
        await self.carregar()
        return rx.toast.success("E-mail atualizado.")

    @rx.event
    async def definir_perfil(self, usuario_id: str, rotulo: str):
        perfil = next((k for k, v in PERFIS.items() if v == rotulo), "")
        auth = await self.get_state(AuthState)
        if not perfil:
            return rx.toast.error("Perfil inválido.")
        if str(auth.auth_user_id) == usuario_id:
            return rx.toast.error("Você não pode alterar o próprio perfil.")
        await admin.definir_perfil(auth.auth_token, int(usuario_id), perfil)
        log.warning("perfil da conta %s alterado para %s por usuario_id=%s", usuario_id, perfil, auth.auth_user_id)
        await self.carregar()
        return rx.toast.success(f"Perfil alterado para {rotulo}.")

    @rx.event
    def abrir_senha(self, usuario_id: str, nome: str):
        self.senha_usuario_id, self.senha_usuario_nome = usuario_id, nome
        self.senha_nova = self.senha_confirmar = self.senha_erro = ""

    @rx.event
    def fechar_senha(self, aberto: bool = False):
        if not aberto:
            self.senha_usuario_id = ""
            self.senha_nova = self.senha_confirmar = ""

    @rx.event
    async def salvar_senha(self):
        if not _senha_valida(self.senha_nova):
            self.senha_erro = _MENSAGEM_SENHA_INVALIDA
            return
        if self.senha_nova != self.senha_confirmar:
            self.senha_erro = "As senhas não coincidem."
            return
        await admin.definir_senha(await self._token_admin(), int(self.senha_usuario_id), self.senha_nova)
        log.warning("senha da conta %s redefinida por um administrador", self.senha_usuario_id)
        nome = self.senha_usuario_nome
        self.fechar_senha(False)
        return rx.toast.success(f"Nova senha definida para {nome}. Informe-a pessoalmente.")

    @rx.event
    async def excluir(self, usuario_id: str):
        auth = await self.get_state(AuthState)
        if str(auth.auth_user_id) == usuario_id:
            return rx.toast.error("Você não pode excluir a própria conta.")
        if len(self.usuarios) <= 1:
            return rx.toast.error("Não é possível excluir o único usuário do sistema.")
        await admin.excluir_usuario(auth.auth_token, int(usuario_id))
        await self.carregar()
        return rx.toast.success("Conta excluída.")
