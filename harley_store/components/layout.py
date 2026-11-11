"""
Layout comum a todas as páginas: menu lateral + moldura da página.

Para adicionar um link novo no menu, basta acrescentar uma linha em
MENU_ITEMS — nada mais precisa mudar aqui. Cores da marca: `tema.py`.
"""

import reflex as rx

from ..state.auth_state import AuthState
from .tema import BORDA, LARANJA, LARANJA_SUAVE, LOGO, PRETO, PRETO_CARTAO

MENU_ITEMS = [
    ("/painel", "layout-dashboard", "Painel"),
    ("/produtos", "package", "Produtos"),
    ("/clientes", "users", "Clientes"),
    ("/motos", "key-round", "Motos dos clientes"),
    ("/vendas", "shopping-cart", "Vendas / Balcão"),
    ("/ordens-servico", "wrench", "Ordens de serviço"),
    ("/compras", "truck", "Compras (entrada)"),
    ("/fornecedores", "factory", "Fornecedores"),
    ("/funcionarios", "id-card", "Funcionários"),
    ("/usuarios", "shield-user", "Usuários do sistema"),
]
SO_ADMIN = {"/usuarios"}


def _menu_link(href: str, icon: str, label: str) -> rx.Component:
    ativo = rx.State.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color=rx.cond(ativo, LARANJA, rx.color("gray", 11))),
            rx.text(label, size="3", display=["none", "none", "block"]),
            spacing="3",
            align="center",
            justify=rx.breakpoints(initial="center", md="start"),
            width="100%",
            padding="0.55rem 0.75rem",
            border_radius="0.5rem",
            border_left=rx.cond(ativo, f"3px solid {LARANJA}", "3px solid transparent"),
            background=rx.cond(ativo, LARANJA_SUAVE, "transparent"),
            color=rx.cond(ativo, "white", rx.color("gray", 11)),
            _hover={"background": LARANJA_SUAVE, "color": "white"},
        ),
        href=href,
        underline="none",
        width="100%",
        title=label,
    )


def sidebar() -> rx.Component:
    """Menu lateral. Em telas estreitas (celular) encolhe para uma trilha só
    de ícones, já que o app agora também roda instalado como PWA no iPhone."""
    return rx.box(
        rx.vstack(
            rx.link(
                rx.image(
                    src=LOGO,
                    alt="Harley-Davidson",
                    width=["44px", "44px", "190px"],
                    height="auto",
                    style={"mixBlendMode": "lighten"},
                ),
                href="/painel",
                padding_bottom="0.75rem",
                align_self="center",
            ),
            *[
                # itens só de administrador ficam ocultos para os demais (a regra vale no servidor)
                rx.cond(AuthState.eh_admin, _menu_link(href, icon, label)) if href in SO_ADMIN
                else _menu_link(href, icon, label)
                for href, icon, label in MENU_ITEMS
            ],
            rx.spacer(),
            rx.box(height="1px", width="100%", background=BORDA),
            rx.hstack(
                rx.icon("circle-user-round", size=18, color=LARANJA),
                rx.text(
                    AuthState.usuario_logado,
                    size="2",
                    color=rx.color("gray", 11),
                    display=["none", "none", "block"],
                ),
                align="center",
                spacing="2",
                width="100%",
                padding="0.4rem 0.75rem",
            ),
            rx.button(
                rx.icon("log-out", size=16),
                rx.text("Sair", display=["none", "none", "block"]),
                on_click=AuthState.sair,
                variant="soft",
                color_scheme="red",
                width="100%",
            ),
            align="start",
            width="100%",
            spacing="1",
            height="100%",
            overflow_y="auto",
        ),
        width=["64px", "64px", "230px"],
        min_width=["64px", "64px", "230px"],
        height="100vh",
        position="sticky",
        top="0",
        padding=["0.5rem", "0.5rem", "1rem"],
        border_right=f"1px solid {BORDA}",
        background=PRETO_CARTAO,
        flex_shrink="0",
    )


def page(*children: rx.Component, title: str, subtitle: str = "") -> rx.Component:
    """Moldura padrão usada em todas as páginas: sidebar + cabeçalho + conteúdo."""
    header_children = [
        rx.heading(title, size="7", weight="bold", letter_spacing="0.02em"),
        rx.box(height="3px", width="48px", background=LARANJA, border_radius="2px"),
    ]
    if subtitle:
        header_children.append(rx.text(subtitle, color=rx.color("gray", 10), size="3"))

    return rx.hstack(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.vstack(*header_children, align="start", spacing="2", padding_bottom="1.25rem"),
                *children,
                align="start",
                width="100%",
                spacing="4",
            ),
            padding=["1rem", "1rem", "2rem"],
            width="100%",
            max_width="1200px",
            overflow_x="auto",
        ),
        align="start",
        width="100%",
        min_height="100vh",
        spacing="0",
        background=PRETO,
    )
