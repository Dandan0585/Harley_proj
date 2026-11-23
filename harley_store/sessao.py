"""
Proteção das ações no SERVIDOR.

O `on_load` com `AuthState.exigir_login` só protege a abertura das páginas.
No Reflex, porém, qualquer event handler (salvar, excluir, cancelar venda...)
pode ser disparado direto pelo websocket, sem abrir página nenhuma. Este
middleware roda antes de TODO evento e, se ele pertence a um state
protegido (qualquer state do app fora `AuthState`), exige uma sessão
conferida no Xano (`AuthState.validar_sessao`). Sem sessão, o evento não
roda e o navegador é mandado para o login.

Telas só de administrador (lista `so_admin`): depois de confirmada a
sessão, um evento desses states (carregar, buscar, salvar, excluir...)
vindo de quem não tem o perfil admin é descartado. A página mostra o
aviso de falta de permissão (`page(..., so_admin=True)`), então não há
toast. O perfil vem do Xano (`AuthState.perfil`), nunca do navegador.
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
    def __init__(
        self,
        estados_protegidos: list[type[BaseState]],
        so_admin: list[type[BaseState]] = (),
    ):
        self._so_admin = {estado.get_full_name() for estado in so_admin}
        self._protegidos = {estado.get_full_name() for estado in estados_protegidos} | self._so_admin

    async def preprocess(self, app, state: BaseState, event: Event) -> StateUpdate | None:
        nome_estado = event.name.rpartition(".")[0]
        if nome_estado not in self._protegidos:
            return None
        auth = await state.get_state(AuthState)
        situacao = await auth.validar_sessao()
        if situacao == SESSAO_OK:
            if nome_estado in self._so_admin and not auth.eh_admin:
                log.warning(
                    "evento de tela de administrador recusado: %s (usuario_id=%s)",
                    event.name.rpartition(".")[2], auth.auth_user_id,
                )
                return StateUpdate(final=True)
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
