import reflex as rx

from ..components.tema import LARANJA, LARANJA_ESCURO, LOGO, PRETO, PRETO_CARTAO
from ..state.auth_state import AuthState


def _campo(rotulo: str, value: rx.Var, on_change, tipo: str = "text") -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="2", weight="bold", color="white"),
        rx.input(
            value=value,
            on_change=on_change,
            type=tipo,
            width="100%",
            size="3",
            style={
                "backgroundColor": "#0d0d0d",
                "color": "#ffffff",
                "border": "1px solid #3a3a3a",
                "caretColor": LARANJA,
            },
            _focus={"border_color": LARANJA, "outline": "none"},
        ),
        spacing="1",
        width="100%",
        align="start",
    )


def _formulario_entrar() -> rx.Component:
    return rx.vstack(
        _campo("Email", AuthState.login_email, AuthState.set_login_email, tipo="email"),
        _campo("Senha", AuthState.login_senha, AuthState.set_login_senha, tipo="password"),
        rx.cond(
            AuthState.login_erro != "",
            rx.text(AuthState.login_erro, color="#ff6b6b", size="2", role="alert"),
        ),
        rx.cond(
            AuthState.login_sucesso != "",
            rx.hstack(
                rx.icon("circle-check", size=16, color="#4ade80"),
                rx.text(AuthState.login_sucesso, color="#4ade80", size="2"),
                spacing="2",
                align="center",
            ),
        ),
        rx.button(
            "Entrar",
            on_click=AuthState.fazer_login,
            width="100%",
            size="3",
            background=LARANJA,
            color="white",
            _hover={"background": LARANJA_ESCURO},
        ),
        rx.text(
            "Esqueci minha senha",
            on_click=AuthState.definir_aba("esqueci"),
            size="2",
            color=LARANJA,
            cursor="pointer",
            align_self="center",
            _hover={"text_decoration": "underline"},
        ),
        spacing="3",
        width="100%",
    )


def _formulario_esqueci() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("key-round", size=20, color=LARANJA),
            rx.heading("Esqueceu a senha?", size="5", color="white"),
            spacing="2",
            align="center",
        ),
        rx.text(
            "Por segurança, a senha só pode ser redefinida por um administrador do sistema. "
            "Peça a ele para definir uma nova senha para você na tela Usuários do sistema.",
            size="2",
            color="#bbbbbb",
        ),
        rx.hstack(
            rx.icon("arrow-left", size=14),
            rx.text("Voltar para o login", size="2"),
            on_click=AuthState.definir_aba("entrar"),
            color="#bbbbbb",
            cursor="pointer",
            align_self="center",
            align="center",
            spacing="1",
            _hover={"color": "white"},
        ),
        spacing="3",
        width="100%",
        align="start",
    )


def login_page() -> rx.Component:
    return rx.theme(
        rx.box(
            rx.center(
                rx.vstack(
                    rx.link(
                        rx.image(
                            src=LOGO,
                            alt="Harley-Davidson",
                            width="260px",
                            height="auto",
                            style={"mixBlendMode": "lighten"},
                        ),
                        href="/",
                        title="Voltar à tela inicial",
                    ),
                    rx.text(
                        "Sistema da loja e da oficina",
                        color="#999999",
                        size="2",
                        padding_bottom="1.5rem",
                    ),
                    rx.box(
                        rx.cond(
                            AuthState.aba_atual == "esqueci",
                            _formulario_esqueci(),
                            rx.vstack(
                                rx.heading("Entrar", size="5", color="white"),
                                _formulario_entrar(),
                                spacing="4",
                                width="100%",
                            ),
                        ),
                        background=PRETO_CARTAO,
                        border=f"1px solid {LARANJA}",
                        border_radius="0.75rem",
                        padding="2rem",
                        width="100%",
                        max_width="380px",
                        box_shadow="0 0 40px rgba(247, 101, 17, 0.15)",
                    ),
                    spacing="1",
                    align="center",
                    width="100%",
                    padding_x="1rem",
                ),
                width="100%",
                height="100vh",
            ),
            width="100%",
            height="100vh",
            background=f"radial-gradient(circle at 50% 20%, #1f1f1f 0%, {PRETO} 60%)",
        ),
        appearance="dark",
        accent_color="orange",
        radius="medium",
        has_background=False,
    )
