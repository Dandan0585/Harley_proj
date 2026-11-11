"""
Botão "Imprimir" usado nas listas de Vendas, Ordens de serviço, Compras e
Motos da loja. Abre o documento em uma nova aba (/imprimir/<tipo>/<id>),
sem tirar o usuário da tela em que está.
"""

import reflex as rx


def botao_imprimir(tipo: str, registro_id, rotulo: str = "Imprimir") -> rx.Component:
    return rx.link(
        rx.button(rx.icon("printer", size=14), rotulo, size="1", variant="soft", color_scheme="gray"),
        href=f"/imprimir/{tipo}/{registro_id}",
        is_external=True,
        underline="none",
    )
