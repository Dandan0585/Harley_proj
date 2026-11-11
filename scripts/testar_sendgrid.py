"""
Confere se o SendGrid está pronto para os e-mails aos clientes.

Uso (PowerShell, na pasta do projeto):
    .venv\\Scripts\\python.exe scripts\\testar_sendgrid.py

Passos:
1. SENDGRID_API_KEY e SENDGRID_REMETENTE estão no .env?
2. A chave é aceita pelo SendGrid e tem permissão de envio ("mail.send")?
3. O remetente está verificado no SendGrid (sem isso, o envio é recusado)?
4. (opcional) Envia um e-mail de teste, com o mesmo modelo do e-mail de
   boas-vindas, para o endereço que você digitar.
A chave nunca é mostrada na tela.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harley_store import email_clientes  # noqa: E402
from harley_store import xano_client  # noqa: E402,F401  (carrega o .env)

API = "https://api.sendgrid.com/v3"


def ok(texto: str) -> None:
    print(f"  [OK]   {texto}")


def falha(texto: str) -> None:
    print(f"  [FALHA] {texto}")


async def main() -> int:
    print("1. Configuração no .env")
    chave, remetente = os.environ.get("SENDGRID_API_KEY", ""), os.environ.get("SENDGRID_REMETENTE", "")
    if not chave or not remetente:
        falha("faltam SENDGRID_API_KEY e/ou SENDGRID_REMETENTE no .env (veja o README, seção "
              "\"E-mails aos clientes (SendGrid)\"). Sem elas, o app não envia e-mails.")
        return 1
    ok(f"chave e remetente configurados (remetente: {remetente})")

    cabecalho = {"Authorization": f"Bearer {chave}"}
    async with httpx.AsyncClient(timeout=20) as cliente:
        print("2. Chave da API")
        r = await cliente.get(f"{API}/scopes", headers=cabecalho)
        if r.status_code == 401:
            falha("o SendGrid recusou a chave (inválida, apagada ou copiada pela metade).")
            return 1
        if r.status_code >= 400:
            falha(f"o SendGrid respondeu HTTP {r.status_code}: {r.text[:200]}")
            return 1
        escopos = r.json().get("scopes", [])
        if "mail.send" not in escopos:
            falha("a chave existe, mas não tem a permissão \"Mail Send\". Crie outra com essa permissão.")
            return 1
        ok("chave aceita, com permissão de envio")

        print("3. Remetente verificado")
        r = await cliente.get(f"{API}/verified_senders", headers=cabecalho)
        if r.status_code < 400:
            verificados = [s.get("from_email", "").lower() for s in r.json().get("results", []) if s.get("verified")]
            if remetente.lower() in verificados:
                ok(f"{remetente} está verificado")
            else:
                falha(f"{remetente} não aparece como remetente verificado (Settings > Sender Authentication). "
                      "Se vocês autenticaram o domínio inteiro, o envio ainda pode funcionar: teste no passo 4.")
        else:
            print(f"  [AVISO] não foi possível listar os remetentes (HTTP {r.status_code}); teste no passo 4.")

    print("4. E-mail de teste")
    destino = input("  Enviar um e-mail de teste para (Enter para pular): ").strip()
    if not destino:
        print("  pulado.")
        return 0
    paragrafos = ["Este é um e-mail de teste do sistema Harley Store.",
                  "Se você recebeu esta mensagem, os e-mails aos clientes estão funcionando."]
    async with httpx.AsyncClient(timeout=20) as cliente:
        r = await cliente.post(f"{API}/mail/send", headers=cabecalho, json={
            "personalizations": [{"to": [{"email": destino}]}],
            "from": {"email": remetente, "name": os.environ.get("SENDGRID_REMETENTE_NOME") or "Harley Store"},
            "subject": "Teste de e-mail - Harley Store",
            "content": [{"type": "text/plain", "value": "\n\n".join(paragrafos)},
                        {"type": "text/html", "value": email_clientes._modelo_html("Teste de e-mail", paragrafos)}],
        })
    if r.status_code == 202:
        ok(f"o SendGrid aceitou o envio para {destino}. Confira a caixa de entrada (e o spam) em alguns minutos.")
        return 0
    falha(f"o SendGrid recusou o envio (HTTP {r.status_code}): {r.text[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
