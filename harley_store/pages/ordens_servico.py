import reflex as rx

from ..components.botao_imprimir import botao_imprimir
from ..components.confirm_dialog import confirm_delete_button
from ..components.formulario import mensagem_erro
from ..components.layout import page
from ..constantes import STATUS_OS
from ..state.os_state import OrdensServicoState


def _linha_item_atual(item: dict, indice: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item["produto_nome"]),
        rx.table.cell(item["quantidade"]),
        rx.table.cell(rx.text("R$ ", item["valor_total_item"])),
        rx.table.cell(
            rx.button(
                "Remover",
                size="1",
                variant="soft",
                color_scheme="red",
                on_click=OrdensServicoState.remover_item(indice),
            )
        ),
    )


def _linha_os(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["data_abertura"]),
        rx.table.cell(row["moto_nome"]),
        rx.table.cell(row["mecanico_nome"]),
        rx.table.cell(rx.text(row["qtd_itens"], " item(ns)")),
        rx.table.cell(rx.text("R$ ", row["valor_total"])),
        rx.table.cell(
            rx.select(
                STATUS_OS,
                value=row["status"],
                on_change=lambda valor: OrdensServicoState.mudar_status(row["id"], valor),
                size="1",
            )
        ),
        rx.table.cell(
            rx.hstack(
                botao_imprimir("os", row["id"]),
                confirm_delete_button(
                    OrdensServicoState.excluir_os(row["id"]),
                    item_label="esta ordem de serviço (as peças lançadas voltam ao estoque)",
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Abrir ordem de serviço", size="4"),
            rx.hstack(
                rx.cond(
                    OrdensServicoState.motos_opcoes.length() == 0,
                    rx.callout(
                        "Cadastre a moto do cliente primeiro.",
                        icon="triangle_alert",
                        color_scheme="amber",
                        flex="1",
                    ),
                    rx.select(
                        OrdensServicoState.motos_opcoes,
                        placeholder="Moto",
                        value=OrdensServicoState.moto_selecionada,
                        on_change=OrdensServicoState.set_moto_selecionada,
                        flex="1",
                    ),
                ),
                rx.cond(
                    OrdensServicoState.mecanicos_opcoes.length() == 0,
                    rx.callout(
                        "Cadastre um funcionário do tipo MECANICO primeiro.",
                        icon="triangle_alert",
                        color_scheme="amber",
                        flex="1",
                    ),
                    rx.select(
                        OrdensServicoState.mecanicos_opcoes,
                        placeholder="Mecânico responsável",
                        value=OrdensServicoState.mecanico_selecionado,
                        on_change=OrdensServicoState.set_mecanico_selecionado,
                        flex="1",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            rx.divider(),
            rx.text("Peças usadas no serviço (opcional)", size="2", weight="bold"),
            rx.flex(
                rx.select(
                    OrdensServicoState.produtos_opcoes,
                    placeholder="Peça",
                    value=OrdensServicoState.item_produto_selecionado,
                    on_change=OrdensServicoState.definir_item_produto,
                    flex="1",
                ),
                rx.input(
                    placeholder="Qtd.",
                    type="number",
                    value=OrdensServicoState.item_quantidade,
                    on_change=OrdensServicoState.definir_item_quantidade,
                    width="110px",
                    flex_shrink="0",
                ),
                rx.input(
                    placeholder="Valor total (R$)",
                    type="number",
                    value=OrdensServicoState.item_valor_total,
                    on_change=OrdensServicoState.set_item_valor_total,
                    width="160px",
                    flex_shrink="0",
                ),
                rx.button(
                    "Adicionar peça",
                    variant="soft",
                    on_click=OrdensServicoState.adicionar_item,
                    flex_shrink="0",
                ),
                gap="3",
                width="100%",
                wrap="wrap",
            ),
            rx.text("Serviços / mão de obra (opcional)", size="2", weight="bold"),
            rx.flex(
                rx.input(
                    placeholder="Descrição do serviço (ex.: revisão de 10.000 km)",
                    value=OrdensServicoState.servico_descricao,
                    on_change=OrdensServicoState.set_servico_descricao,
                    flex="1",
                    min_width="220px",
                ),
                rx.input(
                    placeholder="Valor (R$)",
                    input_mode="decimal",
                    value=OrdensServicoState.servico_valor,
                    on_change=OrdensServicoState.set_servico_valor,
                    width="160px",
                    flex_shrink="0",
                ),
                rx.button(
                    "Adicionar serviço",
                    variant="soft",
                    on_click=OrdensServicoState.adicionar_servico,
                    flex_shrink="0",
                ),
                gap="3",
                width="100%",
                wrap="wrap",
            ),
            rx.cond(
                OrdensServicoState.itens_atual.length() > 0,
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Peça"),
                                rx.table.column_header_cell("Qtd."),
                                rx.table.column_header_cell("Valor"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(rx.foreach(OrdensServicoState.itens_atual, _linha_item_atual)),
                        width="100%",
                        variant="surface",
                    ),
                    rx.hstack(
                        rx.text("Total de peças:", weight="bold"),
                        rx.text("R$ ", OrdensServicoState.total_atual, weight="bold"),
                        spacing="2",
                    ),
                    width="100%",
                    spacing="3",
                ),
            ),
            mensagem_erro(OrdensServicoState.erro_os),
            rx.button(rx.icon("check", size=16), "Abrir OS", on_click=OrdensServicoState.abrir_os, size="3"),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def ordens_servico_page() -> rx.Component:
    return page(
        _formulario(),
        rx.heading("Ordens de serviço", size="4"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Abertura"),
                    rx.table.column_header_cell("Moto"),
                    rx.table.column_header_cell("Mecânico"),
                    rx.table.column_header_cell("Peças"),
                    rx.table.column_header_cell("Valor peças"),
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(OrdensServicoState.ordens, _linha_os)),
            width="100%",
            variant="surface",
        ),
        title="Ordens de serviço",
        subtitle="Oficina: abertura, peças usadas e acompanhamento do status.",
    )
