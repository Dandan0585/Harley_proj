"""
Registro de erros (logs) e mensagens amigáveis para o usuário.

- `configurar_logs()`: os módulos do app usam `logging.getLogger("harley_store...")`.
  A saída vai para o terminal, e na produção o `iniciar_producao.ps1` já
  a grava em logs/producao-AAAAMMDD.log. Formato: data/hora, nível,
  módulo e mensagem. Nunca registre senhas nem tokens.
- `tratar_erro_backend()`: substitui o tratador padrão do Reflex, que mostra
  "An error occurred" (em inglês, e com detalhes técnicos em modo dev). Aqui
  o erro completo vai para o log e o funcionário vê uma mensagem clara.
"""

from __future__ import annotations

import logging
import sys

import httpx
import reflex as rx

log = logging.getLogger("harley_store.erros")


def configurar_logs() -> None:
    raiz = logging.getLogger("harley_store")
    if raiz.handlers:
        return
    saida = logging.StreamHandler(sys.stderr)
    saida.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    raiz.addHandler(saida)
    raiz.setLevel(logging.INFO)
    raiz.propagate = False


def mensagem_amigavel(erro: BaseException) -> str:
    if isinstance(erro, httpx.HTTPStatusError):
        codigo = erro.response.status_code
        if codigo == 429:
            return "O servidor de dados está ocupado. Aguarde alguns segundos e tente de novo."
        if codigo in (400, 409, 422):
            texto = erro.response.text.lower()
            if "unique" in texto or "duplicate" in texto or "already" in texto:
                return "Já existe um registro com esses dados (documento, placa ou chassi repetido)."
            return "O servidor de dados recusou as informações. Confira os campos e tente de novo."
        if codigo == 404:
            return "O registro não existe mais (pode ter sido excluído por outra pessoa). Atualize a página."
        if codigo in (401, 403):
            return "Você não tem permissão para esta operação. Entre novamente."
        return "O servidor de dados respondeu com erro. Tente de novo em instantes."
    if isinstance(erro, httpx.TransportError):
        return "Sem conexão com o servidor de dados. Verifique a internet e tente de novo."
    return "Algo deu errado nesta operação. Nada foi perdido; tente de novo e, se continuar, avise o responsável pelo sistema."


def tratar_erro_backend(exception: Exception):
    log.error("erro nao tratado em um evento", exc_info=exception)
    return rx.toast.error(
        mensagem_amigavel(exception),
        id="erro_backend",
        position="top-center",
        duration=8000,
    )
