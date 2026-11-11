import reflex as rx

from ..components.confirm_dialog import confirm_delete_button
from ..components.formulario import campo, mensagem_erro
from ..components.layout import page
from ..state.auth_state import AuthState
from ..state.usuarios_state import PERFIS, UsuariosState


def _linha(row: dict) -> rx.Component:
    eh_voce = AuthState.auth_user_id.to(str) == row["id"]
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(row["nome"]),
                rx.cond(eh_voce, rx.badge("você", variant="soft", color_scheme="orange")),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.input(
                placeholder="email@exemplo.com",
                default_value=row["email"],
                on_blur=UsuariosState.atualizar_email(row["id"]),
                size="1",
                width="100%",
                min_width="200px",
                aria_label="E-mail",
            )
        ),
        rx.table.cell(
            rx.cond(
                eh_voce,
                rx.badge(row["perfil"], variant="soft"),
                rx.select(
                    list(PERFIS.values()),
                    value=row["perfil"],
                    on_change=lambda valor: UsuariosState.definir_perfil(row["id"], valor),
                    size="1",
                    aria_label="Perfil",
                ),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("key-round", size=14),
                    "Nova senha",
                    size="1",
                    variant="soft",
                    on_click=UsuariosState.abrir_senha(row["id"], row["nome"]),
                ),
                rx.cond(
                    eh_voce,
                    rx.fragment(),
                    confirm_delete_button(
                        UsuariosState.excluir(row["id"]),
                        item_label=f"a conta de “{row['nome']}”",
                    ),
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Nova conta de acesso", size="4"),
            rx.flex(
                campo(
                    "Nome completo",
                    rx.input(
                        value=UsuariosState.novo_nome_completo,
                        on_change=UsuariosState.set_novo_nome_completo,
                        width="100%",
                    ),
                    obrigatorio=True,
                ),
                campo(
                    "E-mail (usado para entrar)",
                    rx.input(
                        type="email",
                        value=UsuariosState.novo_email,
                        on_change=UsuariosState.set_novo_email,
                        width="100%",
                    ),
                    obrigatorio=True,
                ),
                gap="3",
                width="100%",
                flex_direction=["column", "column", "row"],
            ),
            rx.flex(
                campo(
                    "Senha",
                    rx.input(
                        type="password",
                        value=UsuariosState.nova_senha,
                        on_change=UsuariosState.set_nova_senha,
                        width="100%",
                    ),
                    obrigatorio=True,
                ),
                campo(
                    "Confirmar senha",
                    rx.input(
                        type="password",
                        value=UsuariosState.nova_confirmar_senha,
                        on_change=UsuariosState.set_nova_confirmar_senha,
                        width="100%",
                    ),
                    obrigatorio=True,
                ),
                gap="3",
                width="100%",
                flex_direction=["column", "column", "row"],
            ),
            rx.text("Mínimo de 8 caracteres, com letras e números. A conta nasce com perfil Funcionário.",
                    size="1", color=rx.color("gray", 10)),
            mensagem_erro(UsuariosState.erro),
            rx.hstack(
                rx.button(rx.icon("check", size=16), "Criar conta", on_click=UsuariosState.salvar),
                rx.button(
                    rx.icon("x", size=16),
                    "Limpar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=UsuariosState.limpar_formulario,
                ),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _dialogo_senha() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Definir nova senha"),
            rx.dialog.description(
                rx.text("Conta de ", rx.text.strong(UsuariosState.senha_usuario_nome),
                        ". Informe a nova senha à pessoa pessoalmente."),
                size="2",
            ),
            rx.vstack(
                campo("Nova senha", rx.input(type="password", value=UsuariosState.senha_nova,
                                             on_change=UsuariosState.set_senha_nova, width="100%"),
                      obrigatorio=True),
                campo("Repetir nova senha", rx.input(type="password", value=UsuariosState.senha_confirmar,
                                                     on_change=UsuariosState.set_senha_confirmar, width="100%"),
                      obrigatorio=True),
                mensagem_erro(UsuariosState.senha_erro),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancelar", variant="soft", color_scheme="gray")),
                    rx.button("Salvar senha", on_click=UsuariosState.salvar_senha),
                    justify="end",
                    width="100%",
                    spacing="3",
                ),
                spacing="3",
                padding_top="0.75rem",
            ),
            max_width="420px",
        ),
        open=UsuariosState.senha_usuario_id != "",
        on_open_change=UsuariosState.fechar_senha,
    )


def usuarios_page() -> rx.Component:
    return page(
        rx.cond(
            UsuariosState.sem_permissao,
            rx.callout(
                "Esta tela é só para administradores do sistema. Peça a um administrador para "
                "criar contas, redefinir senhas ou mudar perfis.",
                icon="shield-alert",
                color_scheme="amber",
                width="100%",
            ),
            rx.fragment(
                _formulario(),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Nome completo"),
                                rx.table.column_header_cell("E-mail"),
                                rx.table.column_header_cell("Perfil"),
                                rx.table.column_header_cell("Ações"),
                            )
                        ),
                        rx.table.body(rx.foreach(UsuariosState.usuarios, _linha)),
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    overflow_x="auto",
                ),
                _dialogo_senha(),
            ),
        ),
        title="Usuários do sistema",
        subtitle="Contas de acesso: criar, redefinir senha, definir perfil e remover acessos.",
    )
