"""
Confere se a integração com o Asaas (cobranças das vendas) está pronta.

Uso (PowerShell, na pasta do projeto):
    .venv\\Scripts\\python.exe scripts\\testar_asaas.py
    .venv\\Scripts\\python.exe scripts\\testar_asaas.py --cobranca-teste

Passos:
1. ASAAS_API_KEY e ASAAS_AMBIENTE (sandbox) estão no .env?
2. A chave é aceita pelo Asaas (consulta o saldo da conta)?
3. Quantas vendas aguardam pagamento no sistema?
4. (com --cobranca-teste) Cria um cliente TESTE e um boleto TESTE de R$ 5,00
   no Sandbox, mostra o link e REMOVE a cobrança ao final. O cliente TESTE
   pode ser removido no painel do Asaas (Clientes).
A chave nunca é mostrada na tela.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harley_store import asaas_client  # noqa: E402  (carrega o .env)
from harley_store import pagamentos_servico as pagamentos  # noqa: E402
from harley_store import xano_client  # noqa: E402

CPF_TESTE = "52998224725"  # CPF válido de exemplo, aceito pelo Sandbox


def ok(texto: str) -> None:
    print(f"  [OK]   {texto}")


def falha(texto: str) -> None:
    print(f"  [FALHA] {texto}")


async def main() -> int:
    print("1. Configuração no .env")
    if not (os.environ.get("ASAAS_API_KEY") or "").strip():
        falha("falta ASAAS_API_KEY no .env (veja o README, seção \"Pagamentos pelo Asaas\"). "
              "Sem ela, só a forma \"Na loja\" fica disponível.")
        return 1
    if not asaas_client.configurado():
        falha("ASAAS_AMBIENTE precisa ser sandbox nesta versão.")
        return 1
    ok(f"chave configurada; ambiente: {asaas_client.URLS['sandbox']}")

    print("2. Chave da API")
    try:
        saldo = await asaas_client.saldo()
    except asaas_client.FalhaAsaas as erro:
        falha(str(erro))
        return 1
    ok(f"o Asaas aceitou a chave (saldo da conta Sandbox: R$ {float(saldo.get('balance') or 0):.2f})")

    print("3. Vendas aguardando pagamento")
    try:
        vendas = await xano_client.listar("transacoes")
        abertas = [v for v in vendas if v.get("situacao_pagamento") in pagamentos.EM_ABERTO]
        ok(f"{len(abertas)} venda(s) com cobrança em aberto")
        if vendas and "forma_pagamento" not in vendas[0]:
            falha("o Xano ainda não tem os campos de pagamento: rode .\\scripts\\aplicar_xano.ps1")
    except Exception as erro:
        falha(f"não foi possível ler as vendas no Xano: {erro!r}")

    if "--cobranca-teste" not in sys.argv:
        print("\nTudo certo. Para criar um boleto TESTE no Sandbox: scripts\\testar_asaas.py --cobranca-teste")
        return 0

    print("4. Cobrança TESTE no Sandbox")
    try:
        cliente = await asaas_client.buscar_cliente_por_cpf(CPF_TESTE) or await asaas_client.criar_cliente(
            {"name": "TESTE Harley Store", "cpfCnpj": CPF_TESTE, "notificationDisabled": True})
        cobranca = await asaas_client.criar_cobranca({
            "customer": cliente["id"], "billingType": "BOLETO", "value": 5.0,
            "dueDate": pagamentos.vencimento_padrao(), "description": "TESTE - pode ser removida",
            "externalReference": "teste-harley-store",
        })
        ok(f"boleto TESTE criado: {cobranca.get('invoiceUrl')}")
        await asaas_client.cancelar_cobranca(cobranca["id"])
        ok("boleto TESTE removido")
    except asaas_client.FalhaAsaas as erro:
        falha(str(erro))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
