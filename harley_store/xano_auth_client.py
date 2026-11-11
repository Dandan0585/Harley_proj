"""
Cliente HTTP para o grupo "Authentication" do Xano: login e conferência do
token (`auth/me`).

Não há cadastro público nem "esqueci minha senha" sem confirmação: antes,
qualquer pessoa criava uma conta ou trocava a senha de qualquer conta
sabendo só o e-mail. Contas e senhas agora são geridas por um administrador
na tela Usuários (xano_admin_client.py).

A lógica de retentativa em erro 429 é reaproveitada de `xano_client._request`.
"""

from __future__ import annotations

from . import xano_client

BASE_URL = xano_client.AUTH_URL


class XanoAuthError(Exception):
    """Erro retornado pelo Xano (mensagem já pronta pra decidir o que mostrar)."""


class SessaoInvalida(XanoAuthError):
    """O Xano recusou o token (vencido, forjado ou de conta excluída)."""


async def login(email: str, senha: str) -> dict:
    """Retorna {"authToken", "user_id", "name"}. Levanta XanoAuthError em credenciais inválidas."""
    resposta = await xano_client._request(
        "POST", f"{BASE_URL}/auth/login", autenticar=False, json={"email": email, "password": senha}
    )
    if resposta.status_code >= 400:
        try:
            mensagem = resposta.json().get("message", "")
        except ValueError:
            mensagem = ""
        raise XanoAuthError(mensagem or f"Erro {resposta.status_code} no login")
    return resposta.json()


async def me(token: str) -> dict:
    """Confere o token no Xano e devolve {"id", "name", "email", "role", ...}.
    Levanta SessaoInvalida se o Xano recusar o token; erros de rede ou do
    Xano fora do ar sobem como exceções comuns (httpx), para quem chama
    poder diferenciar "sessão inválida" de "não foi possível conferir"."""
    resposta = await xano_client._request(
        "GET", f"{BASE_URL}/auth/me", autenticar=False, headers={"Authorization": f"Bearer {token}"}
    )
    if resposta.status_code in (401, 403):
        raise SessaoInvalida("Sessão inválida ou expirada.")
    resposta.raise_for_status()
    usuario = resposta.json() or {}
    if not usuario.get("id"):
        raise SessaoInvalida("Sessão sem usuário.")
    return usuario
