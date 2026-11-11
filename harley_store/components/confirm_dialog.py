"""
Botão de excluir com confirmação (rx.alert_dialog).

Usado em todas as telas de cadastro no lugar de um `rx.button` de exclusão
direto, para evitar apagar um registro sem querer com um clique único.
"""

from typing import Any

import reflex as rx


def confirm_delete_button(on_confirm: Any, item_label: str = "este registro") -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                rx.icon("trash-2", size=14),
                "Excluir",
                size="1",
                variant="soft",
                color_scheme="red",
            ),
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title("Confirmar exclusão"),
            rx.alert_dialog.description(
                f"Tem certeza que deseja excluir {item_label}? Essa ação não pode ser desfeita."
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Cancelar", variant="soft", color_scheme="gray"),
                ),
                rx.alert_dialog.action(
                    rx.button("Excluir", color_scheme="red", on_click=on_confirm),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="0.5rem",
            ),
        ),
    )
