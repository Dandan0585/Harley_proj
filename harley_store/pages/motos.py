import reflex as rx

from ..components.confirm_dialog import confirm_delete_button
from ..components.formulario import lista_vazia, mensagem_erro
from ..components.layout import page
from ..state.motos_state import MotosState


def _miniatura(row: dict) -> rx.Component:
    return rx.cond(
        row["imagem_url"] != "",
        rx.image(
            src=row["imagem_url"],
            alt=row["modelo"],
            loading="lazy",
            width="96px",
            height="58px",
            border_radius="0.4rem",
            # foto oficial (perfil em fundo branco) aparece inteira; foto da loja preenche
            object_fit=rx.cond(row["foto_oficial"], "contain", "cover"),
            background="white",
            title=rx.cond(row["foto_oficial"], "Foto oficial do modelo (Harley-Davidson)", "Foto da moto"),
        ),
        rx.box(
            rx.icon("bike", size=18, color=rx.color("gray", 8)),
            width="96px",
            height="58px",
            border_radius="0.4rem",
            background=rx.color("gray", 3),
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(_miniatura(row)),
        rx.table.cell(row["modelo"]),
        rx.table.cell(row["placa"]),
        rx.table.cell(row["chassi"]),
        rx.table.cell(row["cliente_nome"]),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    size="1",
                    variant="soft",
                    on_click=MotosState.editar(row),
                ),
                confirm_delete_button(
                    MotosState.excluir(row["id"]),
                    item_label=f"a moto “{row['modelo']}” ({row['placa']})",
                ),
                spacing="2",
            )
        ),
    )


def _campo_imagem() -> rx.Component:
    return rx.vstack(
        rx.text("Foto da moto (opcional)", size="2", weight="bold"),
        rx.hstack(
            rx.cond(
                MotosState.imagem != "",
                rx.image(
                    src=MotosState.imagem_url,
                    width="90px",
                    height="90px",
                    border_radius="0.6rem",
                    object_fit="cover",
                ),
                rx.box(
                    rx.icon("bike", size=28, color=rx.color("gray", 8)),
                    width="90px",
                    height="90px",
                    border_radius="0.6rem",
                    background=rx.color("gray", 3),
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
            ),
            rx.vstack(
                rx.upload(
                    rx.hstack(
                        rx.cond(MotosState.enviando_imagem, rx.spinner(size="2"), rx.icon("upload", size=16)),
                        rx.text(rx.cond(MotosState.enviando_imagem, "Enviando...", "Selecionar foto")),
                        spacing="2",
                        align="center",
                    ),
                    id="upload_imagem_moto",
                    accept={
                        "image/png": [".png"],
                        "image/jpeg": [".jpg", ".jpeg"],
                        "image/webp": [".webp"],
                        "image/gif": [".gif"],
                    },
                    max_files=1,
                    multiple=False,
                    on_drop=MotosState.handle_upload_imagem(
                        rx.upload_files(upload_id="upload_imagem_moto")
                    ),
                    border=f"1px dashed {rx.color('gray', 7)}",
                    border_radius="0.5rem",
                    padding="0.6rem 0.9rem",
                    cursor="pointer",
                ),
                rx.cond(
                    MotosState.imagem != "",
                    rx.button(
                        "Remover foto",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=MotosState.remover_imagem,
                    ),
                ),
                spacing="2",
                align="start",
            ),
            spacing="4",
            align="center",
        ),
        rx.cond(
            MotosState.erro_imagem != "",
            rx.text(MotosState.erro_imagem, color="red", size="2"),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(MotosState.form_id, "Editar moto", "Nova moto"), size="4"),
            rx.cond(
                MotosState.clientes_opcoes.length() == 0,
                rx.callout(
                    "Cadastre um cliente primeiro, na página Clientes.",
                    icon="triangle_alert",
                    color_scheme="amber",
                ),
                rx.fragment(
                    rx.select(
                        MotosState.clientes_opcoes,
                        placeholder="Cliente dono da moto",
                        value=rx.cond(
                            MotosState.cliente_selecionado,
                            MotosState.cliente_selecionado,
                            MotosState.clientes_opcoes[0],
                        ),
                        on_change=MotosState.set_cliente_selecionado,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Modelo (ex.: Iron 883)",
                            value=MotosState.modelo,
                            on_change=MotosState.set_modelo,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Placa",
                            value=MotosState.placa,
                            on_change=MotosState.set_placa,
                            width="160px",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Chassi",
                        value=MotosState.chassi,
                        on_change=MotosState.set_chassi,
                        width="100%",
                    ),
                    _campo_imagem(),
                    mensagem_erro(MotosState.erro_form),
                    rx.hstack(
                        rx.button(rx.icon("check", size=16), "Salvar", on_click=MotosState.salvar, disabled=MotosState.enviando_imagem),
                        rx.button(
                            rx.icon("x", size=16),
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=MotosState.novo,
                        ),
                        spacing="3",
                    ),
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        id="form-moto-cliente",
        width="100%",
    )


def motos_page() -> rx.Component:
    return page(
        _formulario(),
        rx.input(
            placeholder="Buscar por modelo, placa, chassi ou cliente...",
            value=MotosState.busca,
            on_change=MotosState.definir_busca,
            max_width="320px",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Foto"),
                    rx.table.column_header_cell("Modelo"),
                    rx.table.column_header_cell("Placa"),
                    rx.table.column_header_cell("Chassi"),
                    rx.table.column_header_cell("Dono"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(MotosState.motos, _linha)),
            width="100%",
            variant="surface",
        ),
        lista_vazia(MotosState.motos, "Nenhuma moto encontrada."),
        title="Motos dos clientes",
        subtitle="Motos que passam pela oficina ou foram compradas na loja.",
    )
