"""
Proteção das ações no SERVIDOR.

O `on_load` com `AuthState.exigir_login` só protege a abertura das páginas.
No Reflex, porém, qualquer event handler (salvar, excluir, cancelar venda...)
pode ser disparado direto pelo websocket, sem abrir página nenhuma. Este
middleware roda antes de TODO evento e, se ele pertence a um state
protegido (qualquer state do app fora `AuthState`), exige uma sessão
conferida no Xano (`AuthState.validar_sessao`). Sem sessão, o evento não
roda e o navegador é mandado para o login.
"""

from __future__ import annotations

import logging

import reflex as rx
from reflex.event import Event, fix_events
from reflex.middleware import Middleware
from reflex.state import BaseState, StateUpdate

from .state.auth_state import SESSAO_INDISPONIVEL, SESSAO_OK, AuthState

log = logging.getLogger("harley_store.sessao")


class ExigeSessaoMiddleware(Middleware):
    def __init__(self, estados_protegidos: list[type[BaseState]]):
        self._protegidos = {estado.get_full_name() for estado in estados_protegidos}

    async def preprocess(self, app, state: BaseState, event: Event) -> StateUpdate | None:
        nome_estado = event.name.rpartition(".")[0]
        if nome_estado not in self._protegidos:
            return None
        auth = await state.get_state(AuthState)
        situacao = await auth.validar_sessao()
        if situacao == SESSAO_OK:
            return None
        log.warning("evento bloqueado sem sessao valida: %s (%s)", event.name.rpartition(".")[2], situacao)
        if situacao == SESSAO_INDISPONIVEL:
            eventos = [rx.toast.error(
                "Sem conexão com o servidor de dados para confirmar seu login. Tente novamente em instantes.",
                id="sessao_indisponivel",
            )]
        else:
            eventos = [AuthState.sessao_expirada]
        return StateUpdate(events=fix_events(eventos, event.token, router_data=event.router_data), final=True)
