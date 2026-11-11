"""
State de autenticação (login e sessão).

Não há cadastro público nem "esqueci minha senha" sem confirmação: contas,
senhas e perfis são geridos por um administrador na tela Usuários.

Login e cadastro usam a tabela `user` do Xano (grupo "Authentication" —
ver `xano_auth_client.py`), não um banco local. Quem está logado é
lembrado por dois cookies (`rx.Cookie`): `usuario_logado` (nome pra
exibir) e `auth_token` (token do Xano, que vence em 24 h; o cookie vence
junto).

O token é CONFERIDO NO XANO (`auth/me`), não basta existir: um cookie
inventado ou vencido leva ao login. A conferência vale por
`REVALIDAR_SEGUNDOS` e é refeita depois disso (cada `auth/me` custa uma
requisição e um registro em `event_log` no Xano Free).

Quem aplica a regra:
- `exigir_login`, primeiro item do `on_load` de toda página protegida;
- `sessao.ExigeSessaoMiddleware`, que barra no SERVIDOR qualquer evento
  dos states protegidos (salvar, excluir...) vindo de quem não tem sessão
  válida, mesmo que a pessoa mande o evento direto pelo websocket.

A identidade (id, nome e perfil) vem do Xano, nunca de cookie editável.
"""

from __future__ import annotations

import logging
import re
import time

import reflex as rx

from .. import xano_auth_client
from ..xano_auth_client import SessaoInvalida, XanoAuthError

log = logging.getLogger("harley_store.auth")

# Tokens do Xano valem 24 h (auth/login e auth/signup: expiration = 86400).
VALIDADE_TOKEN_SEGUNDOS = 86400
REVALIDAR_SEGUNDOS = 600

SESSAO_OK = "ok"
SESSAO_INVALIDA = "invalida"
SESSAO_INDISPONIVEL = "indisponivel"

_SENHA_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def _senha_valida(senha: str) -> bool:
    """Mesma regra de senha exigida pelo Xano: 8+ caracteres, com letra e número."""
    return bool(_SENHA_REGEX.match(senha))


_MENSAGEM_SENHA_INVALIDA = "A senha precisa ter pelo menos 8 caracteres, com letras e números."


class AuthState(rx.State):
    # Nome do usuário logado (só pra exibição) e token do Xano.
    usuario_logado: str = rx.Cookie(
        "", name="hs_usuario", max_age=VALIDADE_TOKEN_SEGUNDOS, same_site="strict"
    )
    auth_token: str = rx.Cookie(
        "", name="hs_auth_token", max_age=VALIDADE_TOKEN_SEGUNDOS, same_site="strict"
    )

    # Identidade conferida no Xano (não é cookie: não pode ser editada no navegador).
    auth_user_id: int = 0
    perfil: str = ""

    # Última conferência do token (só no servidor, não vai para o navegador).
    _token_conferido: str = ""
    _conferido_em: float = 0.0

    # Campos do formulário de login
    login_email: str = ""
    login_senha: str = ""
    login_erro: str = ""

    # Mensagem verde mostrada na aba "Entrar"
    login_sucesso: str = ""

    aba_atual: str = "entrar"  # "entrar" | "esqueci"

    @rx.var
    def esta_logado(self) -> bool:
        return bool(self.auth_token)

    @rx.var
    def eh_admin(self) -> bool:
        return self.perfil == "admin"

    # ------------------------------------------------------------- sessão

    def _registrar_sessao(self, token: str, usuario_id: int, nome: str, perfil: str = "") -> None:
        self.auth_token = token
        self.auth_user_id = int(usuario_id)
        self.usuario_logado = nome
        if perfil:
            self.perfil = perfil
        self._token_conferido = token
        self._conferido_em = time.monotonic()

    def _limpar_sessao(self) -> None:
        self.auth_token = ""
        self.auth_user_id = 0
        self.usuario_logado = ""
        self.perfil = ""
        self._token_conferido = ""
        self._conferido_em = 0.0

    async def validar_sessao(self) -> str:
        """SESSAO_OK, SESSAO_INVALIDA ou SESSAO_INDISPONIVEL (Xano fora do ar
        e o token ainda não foi conferido nesta sessão)."""
        token = self.auth_token
        if not token:
            return SESSAO_INVALIDA
        ja_conferido = token == self._token_conferido
        if ja_conferido and time.monotonic() - self._conferido_em < REVALIDAR_SEGUNDOS:
            return SESSAO_OK
        try:
            usuario = await xano_auth_client.me(token)
        except SessaoInvalida:
            log.info("sessao recusada pelo Xano (usuario_id=%s)", self.auth_user_id or "?")
            self._limpar_sessao()
            return SESSAO_INVALIDA
        except Exception as erro:
            # Xano fora do ar: quem já foi conferido continua trabalhando.
            log.warning("nao foi possivel conferir a sessao: %r", erro)
            return SESSAO_OK if ja_conferido else SESSAO_INDISPONIVEL
        self._registrar_sessao(
            token,
            usuario["id"],
            usuario.get("name") or usuario.get("email") or "",
            usuario.get("role") or "",
        )
        return SESSAO_OK

    @rx.event
    async def exigir_login(self):
        """Chamar no on_load de toda página protegida (primeiro item)."""
        situacao = await self.validar_sessao()
        if situacao == SESSAO_INVALIDA:
            return rx.redirect("/login")
        if situacao == SESSAO_INDISPONIVEL:
            return rx.toast.error(
                "Não foi possível confirmar seu login agora (sem conexão com o servidor de dados). "
                "Tente novamente em instantes.",
                id="sessao_indisponivel",
            )

    @rx.event
    def sessao_expirada(self):
        """Disparado pelo middleware quando um evento chega sem sessão válida."""
        self._limpar_sessao()
        return [
            rx.toast.warning("Sua sessão expirou. Entre novamente.", id="sessao_expirada"),
            rx.redirect("/login"),
        ]

    @rx.event
    async def redirecionar_se_ja_logado(self):
        """Chamar no on_load da página de login — se já estiver logado, pula para o painel."""
        if self.auth_token and await self.validar_sessao() == SESSAO_OK:
            return rx.redirect("/painel")

    # ------------------------------------------------------------- telas

    @rx.event
    def definir_aba(self, aba: str):
        self.aba_atual = aba if aba in ("entrar", "esqueci") else "entrar"
        self.login_erro = ""
        self.login_sucesso = ""

    @rx.event
    async def fazer_login(self):
        email = self.login_email.strip()
        senha = self.login_senha
        if not email or not senha:
            self.login_erro = "Preencha email e senha."
            return

        try:
            resultado = await xano_auth_client.login(email, senha)
        except XanoAuthError:
            log.info("login recusado para %s", email)
            self.login_erro = "Email ou senha incorretos."
            return
        except Exception:
            log.exception("falha de conexao no login")
            self.login_erro = "Não foi possível conectar. Tente novamente em instantes."
            return

        self.login_erro = ""
        self.login_sucesso = ""
        self.login_senha = ""
        perfil = ""
        try:
            perfil = (await xano_auth_client.me(resultado["authToken"])).get("role") or ""
        except Exception:
            log.warning("login sem conferir o perfil (sera lido na proxima validacao)")
        self._registrar_sessao(resultado["authToken"], resultado["user_id"], resultado.get("name") or email, perfil)
        if not perfil:
            self._conferido_em = 0.0  # perfil não lido: confere de novo no próximo evento
        log.info("login usuario_id=%s perfil=%s", resultado["user_id"], perfil or "?")
        return rx.redirect("/painel")

    @rx.event
    def sair(self):
        self._limpar_sessao()
        return rx.redirect("/login")
