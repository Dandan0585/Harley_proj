"""
Repara a conta de serviço do app no Xano ("Sistema Harley Store").

Use quando o app mostrar "Você não tem permissão para esta operação" em todas
as telas e listas vazias: é o sinal de que o login da conta de serviço
(HARLEY_XANO_EMAIL / HARLEY_XANO_SENHA no .env) foi recusado pelo Xano.

Uso (PowerShell, na pasta do projeto):
    .venv\\Scripts\\python.exe scripts\\reparar_conta_servico.py

O script:
1. pede o SEU e-mail e senha de administrador (a senha não aparece na tela);
2. procura a conta de serviço pelo e-mail do .env (e a cria se não existir);
3. gera uma senha nova e forte, grava no Xano e no .env (e no .env da
   produção, C:\\HARLEY_PROD, se existir e você confirmar);
4. testa se a conta consegue ler os dados.
A senha gerada nunca é mostrada na tela. Depois, reinicie o app.
"""

from __future__ import annotations

import asyncio
import getpass
import re
import secrets
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import os  # noqa: E402

from harley_store import xano_admin_client as admin  # noqa: E402
from harley_store import xano_client as xano  # noqa: E402  (carrega o .env)

NOME_CONTA = "Sistema Harley Store"
ENV_PRODUCAO = Path(r"C:\HARLEY_PROD\.env")


def gravar_no_env(arquivo: Path, chaves: dict[str, str]) -> None:
    """Troca (ou acrescenta) as linhas CHAVE=valor, sem mexer no resto do arquivo."""
    linhas = arquivo.read_text(encoding="utf-8").splitlines() if arquivo.exists() else []
    faltando = dict(chaves)
    for i, linha in enumerate(linhas):
        nome = linha.split("=", 1)[0].strip()
        if nome in faltando:
            linhas[i] = f"{nome}={faltando.pop(nome)}"
    linhas += [f"{k}={v}" for k, v in faltando.items()]
    arquivo.write_text("\n".join(linhas) + "\n", encoding="utf-8")


async def login(email: str, senha: str) -> str | None:
    resposta = await xano._request("POST", f"{xano.AUTH_URL}/auth/login",
                                   json={"email": email, "password": senha}, autenticar=False)
    return resposta.json().get("authToken") if resposta.status_code == 200 else None


async def main() -> None:
    email_servico = (os.environ.get("HARLEY_XANO_EMAIL") or "").strip().lower()
    if not email_servico:
        email_servico = input("E-mail para a conta de serviço (ex.: sistema@harleystore.com.br): ").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_servico):
        print("E-mail da conta de serviço inválido.")
        return
    print(f"Conta de serviço: {email_servico}\n")

    print("Entre com a SUA conta de administrador do app:")
    email_admin = input("  E-mail: ").strip()
    token = await login(email_admin, getpass.getpass("  Senha (não aparece ao digitar): "))
    if not token:
        print("\nE-mail ou senha de administrador incorretos. Nada foi alterado.")
        return

    try:
        usuarios = await admin.listar_usuarios(token)
    except admin.SemPermissao:
        print("\nEssa conta não é administradora. Use uma conta com perfil admin. Nada foi alterado.")
        return

    nova_senha = secrets.token_urlsafe(24)
    conta = next((u for u in usuarios if (u.get("email") or "").lower() == email_servico), None)
    if conta:
        await admin.definir_senha(token, int(conta["id"]), nova_senha)
        print(f"Senha da conta de serviço redefinida (id {conta['id']}).")
    else:
        await admin.criar_usuario(token, NOME_CONTA, email_servico, nova_senha)
        print("A conta de serviço não existia: foi criada.")

    gravar_no_env(RAIZ / ".env", {"HARLEY_XANO_EMAIL": email_servico, "HARLEY_XANO_SENHA": nova_senha})
    print(f"Gravado em {RAIZ / '.env'}")
    if ENV_PRODUCAO.exists() and ENV_PRODUCAO.resolve() != (RAIZ / ".env").resolve():
        if input(f"Gravar também em {ENV_PRODUCAO} (produção)? [S/n] ").strip().lower() in ("", "s", "sim"):
            gravar_no_env(ENV_PRODUCAO, {"HARLEY_XANO_EMAIL": email_servico, "HARLEY_XANO_SENHA": nova_senha})
            print(f"Gravado em {ENV_PRODUCAO}")

    # teste: a conta nova consegue entrar e ler os dados?
    os.environ["HARLEY_XANO_EMAIL"], os.environ["HARLEY_XANO_SENHA"] = email_servico, nova_senha
    try:
        clientes = await xano.listar("clientes")
    except Exception as erro:
        print(f"\nATENÇÃO: o teste de leitura falhou ({erro!r}).")
        return
    print(f"\nTudo certo: a conta de serviço leu {len(clientes)} cliente(s) do Xano.")
    print("Agora reinicie o app (feche o terminal do reflex run e rode de novo).")


if __name__ == "__main__":
    asyncio.run(main())
