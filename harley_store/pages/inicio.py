"""
Página inicial (splash) — a primeira coisa que aparece ao abrir o app:
o logo Harley-Davidson sobre fundo preto e um botão para seguir ao login.
Se o usuário já estiver logado, a página de login redireciona direto
para o painel, então o botão serve para os dois casos.
"""

import reflex as rx

from ..components.tema import LARANJA, LARANJA_ESCURO, LOGO, TEXTO_SECUNDARIO

_ANIMACAO = """
@keyframes hs-surgir {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}
"""


def inicio_page() -> rx.Component:
    return rx.theme(
        rx.el.style(_ANIMACAO),
        rx.center(
            rx.vstack(
                rx.image(
                    src=LOGO,
                    alt="Harley-Davidson Motor Cycles",
                    width=["92vw", "80vw", "640px"],
                    max_width="640px",
                    height="auto",
                    # a própria imagem já tem o fundo preto com vinheta;
                    # por isso a página usa preto puro, sem moldura aparente
                    # (o clip corta 1px de borda clara que o arquivo tem)
                    style={"animation": "hs-surgir 0.9s ease-out both", "clipPath": "inset(1px 2px)"},
                ),
                rx.text(
                    "LOJA  •  OFICINA  •  ESTOQUE",
                    color=TEXTO_SECUNDARIO,
                    size="2",
                    letter_spacing="0.35em",
                    weight="bold",
                ),
                rx.link(
                    rx.button(
                        "ENTRAR",
                        rx.icon("arrow-right", size=18),
                        size="4",
                        background=LARANJA,
                        color="white",
                        letter_spacing="0.15em",
                        padding_x="2.5rem",
                        cursor="pointer",
                        _hover={"background": LARANJA_ESCURO},
                    ),
                    href="/login",
                    underline="none",
                    margin_top="1.5rem",
                ),
                align="center",
                spacing="4",
                style={"animation": "hs-surgir 0.9s ease-out both"},
            ),
            width="100%",
            min_height="100vh",
            padding="1rem",
            background="#000000",
        ),
        appearance="dark",
        accent_color="orange",
        has_background=False,
    )
