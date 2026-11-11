"""
Acesso à API do Asaas (https://docs.asaas.com), plataforma de cobranças.

Usado pelas vendas com pagamento por boleto ou cartão (change
pagamento-de-vendas-pelo-asaas, design D1). Só este módulo fala com o
Asaas; as regras ficam em `pagamentos_servico.py`.

Configuração, no arquivo .env da pasta do projeto (fora do git):
    ASAAS_API_KEY=$aact_...          (Integrações > Chaves de API, no painel do Asaas)
    ASAAS_AMBIENTE=sandbox           (só o Sandbox é aceito por enquanto)
    ASAAS_INTERVALO_MINUTOS=5        (opcional: consulta dos pagamentos)
Sem ASAAS_API_KEY, a integração fica desligada e só "Na loja" é oferecido.
A chave nunca vai para o log, para a tela ou para o Xano.
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from . import xano_client  # noqa: F401  (carrega o .env)

log = logging.getLogger("harley_store.asaas")

URLS = {"sandbox": "https://api-sandbox.asaas.com/v3"}
_TIMEOUT = 30.0
_USER_AGENT = "HarleyStore"  # o Asaas exige User-Agent das contas novas
_ESPERA_NOVA_TENTATIVA = 5.0  # segundos
_NOVAS_TENTATIVAS = 3          # ao cancelar uma cobrança recém-criada


class FalhaAsaas(Exception):
    """Erro com mensagem pronta para mostrar ao funcionário."""


def _ambiente() -> str:
    return (os.environ.get("ASAAS_AMBIENTE") or "sandbox").strip().lower()


def configurado() -> bool:
    if not (os.environ.get("ASAAS_API_KEY") or "").strip():
        return False
    if _ambiente() not in URLS:
        log.warning("ASAAS_AMBIENTE=%s não é aceito (use sandbox): integração com o Asaas desligada", _ambiente())
        return False
    return True


def intervalo_minutos() -> float:
    try:
        return max(1.0, float(os.environ.get("ASAAS_INTERVALO_MINUTOS") or 5))
    except ValueError:
        return 5.0


def _mensagem_de_erro(resposta: httpx.Response) -> str:
    """O Asaas responde {"errors": [{"code", "description"}]}."""
    try:
        erros = resposta.json().get("errors") or []
        textos = [e.get("description") for e in erros if e.get("description")]
    except Exception:
        textos = []
    if resposta.status_code == 401:
        return "o Asaas recusou a chave de API (confira ASAAS_API_KEY no .env)"
    return "; ".join(textos) or f"HTTP {resposta.status_code}"


async def _chamar(metodo: str, caminho: str, **kwargs) -> dict:
    if not configurado():
        raise FalhaAsaas("A integração com o Asaas não está configurada no servidor.")
    cabecalhos = {"access_token": os.environ["ASAAS_API_KEY"].strip(), "User-Agent": _USER_AGENT,
                  "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(base_url=URLS[_ambiente()], timeout=_TIMEOUT) as cliente:
            resposta = await cliente.request(metodo, caminho, headers=cabecalhos, **kwargs)
    except httpx.HTTPError as erro:
        log.warning("falha de conexão com o Asaas (%s %s): %r", metodo, caminho, erro)
        raise FalhaAsaas("Não foi possível conectar ao Asaas (falha de conexão).") from erro
    if resposta.status_code >= 400:
        motivo = _mensagem_de_erro(resposta)
        log.error("Asaas recusou %s %s: %s", metodo, caminho, motivo)
        raise FalhaAsaas(f"O Asaas recusou o pedido: {motivo}.")
    return resposta.json() if resposta.content else {}


# ------------------------------------------------------------------ clientes

async def buscar_cliente_por_cpf(cpf_cnpj: str) -> dict | None:
    dados = await _chamar("GET", "/customers", params={"cpfCnpj": cpf_cnpj, "limit": 1})
    clientes = [c for c in dados.get("data") or [] if not c.get("deleted")]
    return clientes[0] if clientes else None


async def criar_cliente(dados: dict) -> dict:
    return await _chamar("POST", "/customers", json=dados)


# ----------------------------------------------------------------- cobranças

async def criar_cobranca(dados: dict) -> dict:
    return await _chamar("POST", "/payments", json=dados)


async def buscar_cobranca(cobranca_id: str) -> dict:
    return await _chamar("GET", f"/payments/{cobranca_id}")


async def buscar_cobranca_por_referencia(referencia: str) -> dict | None:
    dados = await _chamar("GET", "/payments", params={"externalReference": referencia, "limit": 10})
    cobrancas = [c for c in dados.get("data") or [] if not c.get("deleted")]
    return cobrancas[0] if cobrancas else None


async def cancelar_cobranca(cobranca_id: str) -> dict:
    """No Asaas, cancelar uma cobrança em aberto é removê-la (DELETE). Nos
    primeiros segundos depois de criado, o boleto é recusado com "erro
    desconhecido" (conferido no Sandbox em 11/11/2026: liberou em ~10 s):
    tenta de novo até 3 vezes, com 5 s de espera."""
    for tentativa in range(_NOVAS_TENTATIVAS + 1):
        try:
            return await _chamar("DELETE", f"/payments/{cobranca_id}")
        except FalhaAsaas:
            if tentativa == _NOVAS_TENTATIVAS:
                raise
            await asyncio.sleep(_ESPERA_NOVA_TENTATIVA)
    return {}


async def saldo() -> dict:
    """Saldo da conta (usado por scripts/testar_asaas.py para conferir a chave)."""
    return await _chamar("GET", "/finance/balance")
