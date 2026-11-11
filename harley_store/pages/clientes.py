import reflex as rx

from ..components.confirm_dialog import confirm_delete_button
from ..components.formulario import campo, lista_vazia, mensagem_erro
from ..components.layout import page
from ..state.clientes_state import ClientesState


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["nome_cliente"]),
        rx.table.cell(row["cpf_cnpj"]),
        rx.table.cell(row["telefone"]),
        rx.table.cell(row["email"]),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    size="1",
                    variant="soft",
                    on_click=ClientesState.editar(row),
                ),
                confirm_delete_button(
                    ClientesState.excluir(row["id"]),
                    item_label=f"o cliente “{row['nome_cliente']}”",
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(ClientesState.form_id, "Editar cliente", "Novo cliente"), size="4"),
            rx.flex(
                campo(
                    "Nome completo",
                    rx.input(
                        value=ClientesState.nome_cliente,
                        on_change=ClientesState.set_nome_cliente,
                        max_length=120,
                        auto_complete=False,
                        width="100%",
                    ),
                    obrigatorio=True,
                ),
                campo(
                    "CPF ou CNPJ",
                    rx.input(
                        placeholder="000.000.000-00",
                        value=ClientesState.cpf_cnpj,
                        on_change=ClientesState.set_cpf_cnpj,
                        input_mode="numeric",
                        max_length=18,
                        width="100%",
                    ),
                    obrigatorio=True,
                    largura=["100%", "100%", "240px"],
                ),
                gap="3",
                width="100%",
                flex_direction=["column", "column", "row"],
            ),
            rx.flex(
                campo(
                    "Telefone",
                    rx.input(
                        placeholder="(11) 91234-5678",
                        value=ClientesState.telefone,
                        on_change=ClientesState.set_telefone,
                        type="tel",
                        max_length=16,
                        width="100%",
                    ),
                ),
                campo(
                    "E-mail",
                    rx.input(
                        placeholder="nome@exemplo.com.br",
                        value=ClientesState.email,
                        on_change=ClientesState.set_email,
                        type="email",
                        width="100%",
                    ),
                ),
                gap="3",
                width="100%",
                flex_direction=["column", "column", "row"],
            ),
            campo(
                "Endereço",
                rx.input(
                    placeholder="Rua, número, bairro, cidade/UF, CEP",
                    value=ClientesState.endereco,
                    on_change=ClientesState.set_endereco,
                    width="100%",
                ),
            ),
            mensagem_erro(ClientesState.erro_form),
            rx.hstack(
                rx.button(rx.icon("check", size=16), "Salvar", on_click=ClientesState.salvar),
                rx.button(
                    rx.icon("x", size=16),
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=ClientesState.novo,
                ),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        id="form-cliente",
        width="100%",
    )


def clientes_page() -> rx.Component:
    return page(
        _formulario(),
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            placeholder="Buscar por nome, CPF/CNPJ, telefone ou e-mail...",
            value=ClientesState.busca,
            on_change=ClientesState.definir_busca,
            width=["100%", "100%", "420px"],
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Cliente"),
                    rx.table.column_header_cell("CPF/CNPJ"),
                    rx.table.column_header_cell("Telefone"),
                    rx.table.column_header_cell("E-mail"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(ClientesState.clientes, _linha)),
            width="100%",
            variant="surface",
        ),
        lista_vazia(ClientesState.clientes, "Nenhum cliente encontrado."),
        title="Clientes",
        subtitle="Cadastro de clientes da loja e da oficina.",
    )
