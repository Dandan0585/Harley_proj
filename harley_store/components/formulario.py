"""
Peças comuns dos formulários, para todas as telas terem o mesmo padrão:

- `campo`: rótulo acima do controle, com "*" laranja nos obrigatórios
  (o rótulo continua visível depois de digitar, ao contrário do placeholder);
- `mensagem_erro`: caixa vermelha com o erro de validação, dentro do formulário;
- `lista_vazia`: aviso quando a lista/tabela não tem nada para mostrar.
"""

from typing import Any

import reflex as rx

from .tema import LARANJA


def campo(rotulo: str, *controles: rx.Component, obrigatorio: bool = False, largura: Any = "100%") -> rx.Component:
    return rx.vstack(
        rx.text(
            rotulo,
            rx.cond(obrigatorio, rx.text.span(" *", color=LARANJA, aria_hidden="true"), rx.fragment()),
            size="2",
            weight="medium",
            color=rx.color("gray", 11),
            as_="label",
        ),
        *controles,
        spacing="1",
        width=largura,
        align="start",
    )


def mensagem_erro(mensagem: rx.Var) -> rx.Component:
    return rx.cond(
        mensagem != "",
        rx.callout(mensagem, icon="triangle-alert", color_scheme="red", size="1", width="100%", role="alert"),
    )


def lista_vazia(lista: rx.Var, texto: str) -> rx.Component:
    return rx.cond(
        lista.length() == 0,
        rx.center(
            rx.vstack(
                rx.icon("inbox", size=28, color=rx.color("gray", 8)),
                rx.text(texto, color=rx.color("gray", 10), size="2"),
                align="center",
                spacing="2",
            ),
            width="100%",
            padding="1.5rem",
        ),
    )
