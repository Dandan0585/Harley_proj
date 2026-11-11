"""
Cliente HTTP para a gestão de contas de acesso (tela "Usuários do sistema").

Todas as chamadas levam o token de QUEM ESTÁ LOGADO, e o Xano confere que
essa pessoa tem perfil "admin" (função Quick Start/enforce_role). Um
funcionário comum recebe 403 mesmo chamando a API direto.

Endpoints: grupo "Admin" (listar, e-mail, senha, perfil, excluir) e
`auth/signup` do grupo "Authentication" (criar conta), ambos só para admin.
A lógica de retentativa em erro 429 é reaproveitada de `xano_client._request`.
"""

from __future__ import annotations

from . import xano_client

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:KegVKtiw"
AUTH_URL = xano_client.AUTH_URL


class SemPermissao(Exception):
    """O Xano recusou: quem está logado não é administrador (ou a sessão venceu)."""


class ErroAdmin(Exception):
    """Recusa do Xano com mensagem (ex.: e-mail já usado)."""


async def _chamar(token: str, metodo: str, url: str, **kwargs):
    resposta = await xano_client._request(
        metodo, url, autenticar=False, headers={"Authorization": f"Bearer {token}"}, **kwargs
    )
    if resposta.status_code in (401, 403):
        raise SemPermissao()
    if resposta.status_code >= 400:
        try:
            mensagem = resposta.json().get("message", "")
        except ValueError:
            mensagem = ""
        if mensagem:
            raise ErroAdmin(mensagem)
        resposta.raise_for_status()
    try:
        dados = resposta.json()
    except ValueError:
        return None
    # A função Quick Start/enforce_role (versão antiga) recusava com `throw`,
    # que o Xano devolve como 200 + {"statement": "Throw Error"}: não é sucesso.
    if isinstance(dados, dict) and dados.get("statement") == "Throw Error":
        raise SemPermissao()
    return dados


async def listar_usuarios(token: str) -> list[dict]:
    return await _chamar(token, "GET", f"{BASE_URL}/user/list") or []


async def criar_usuario(token: str, nome: str, email: str, senha: str) -> dict:
    return await _chamar(token, "POST", f"{AUTH_URL}/auth/signup",
                         json={"name": nome, "email": email, "password": senha})


async def atualizar_email(token: str, usuario_id: int, novo_email: str) -> dict:
    return await _chamar(token, "POST", f"{BASE_URL}/user/update-email",
                         json={"id": usuario_id, "email": novo_email})


async def definir_senha(token: str, usuario_id: int, senha: str) -> None:
    await _chamar(token, "POST", f"{BASE_URL}/user/set-password", json={"id": usuario_id, "password": senha})


async def definir_perfil(token: str, usuario_id: int, perfil: str) -> None:
    await _chamar(token, "POST", f"{BASE_URL}/user/set-role", json={"id": usuario_id, "role": perfil})


async def excluir_usuario(token: str, usuario_id: int) -> None:
    await _chamar(token, "POST", f"{BASE_URL}/user/delete", json={"id": usuario_id})

