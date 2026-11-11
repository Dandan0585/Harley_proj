import reflex as rx

from ..components.botao_imprimir import botao_imprimir
from ..components.layout import page
from ..constantes import TIPOS_VENDA
from ..state.vendas_state import SEM_CLIENTE, VendasState


# ------------------------------------------------------------------ cancelamento

def _dialogo_cancelar(gatilho: rx.Component, titulo, descricao, ao_confirmar) -> rx.Component:
    """Confirmação de cancelamento com motivo opcional (individual ou em lote)."""
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(gatilho),
        rx.alert_dialog.content(
            rx.alert_dialog.title(titulo),
            rx.alert_dialog.description(descricao),
            rx.input(
                placeholder="Motivo do cancelamento (opcional)",
                value=VendasState.motivo_cancelamento,
                on_change=VendasState.set_motivo_cancelamento,
                width="100%",
                margin_top="0.75rem",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(rx.button("Voltar", variant="soft", color_scheme="gray")),
                rx.alert_dialog.action(rx.button("Cancelar venda", color_scheme="red", on_click=ao_confirmar)),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="0.75rem",
            ),
        ),
    )


def _situacao(row: dict) -> rx.Component:
    return rx.cond(
        row["cancelada"],
        rx.vstack(
            rx.badge(rx.icon("ban", size=12), "Cancelada", color_scheme="red", variant="soft"),
            rx.text(row["data_cancelamento"], size="1", color=rx.color("gray", 10)),
            spacing="1",
            align="start",
            title=row["motivo"],
        ),
        rx.badge(rx.icon("circle-check", size=12), "Ativa", color_scheme="green", variant="soft"),
    )


def _pagamento(row: dict) -> rx.Component:
    """Forma e situação do pagamento, com o link da cobrança do Asaas."""
    cor = rx.match(
        row["situacao_pagamento"],
        ("PAGO", "green"),
        ("AGUARDANDO", "blue"),
        ("VENCIDO", "orange"),
        ("SEM_COBRANCA", "red"),
        "gray",
    )
    return rx.vstack(
        rx.text(row["forma"], size="1", color=rx.color("gray", 10)),
        rx.badge(row["pagamento"], color_scheme=cor, variant="soft"),
        rx.cond(row["data_pagamento"] != "",
                rx.text("em ", row["data_pagamento"], size="1", color=rx.color("gray", 10))),
        rx.cond(
            row["link_cobranca"] != "",
            rx.link(rx.hstack(rx.icon("external-link", size=12), rx.text("Abrir cobrança", size="1"), spacing="1",
                              align="center"),
                    href=row["link_cobranca"], is_external=True),
        ),
        rx.cond(
            row["pode_cobrar"],
            rx.button(rx.icon("refresh-cw", size=12), "Gerar cobrança de novo", size="1", variant="soft",
                      color_scheme="orange", on_click=VendasState.gerar_cobranca(row["id"])),
        ),
        spacing="1",
        align="start",
    )


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                row["cancelada"],
                rx.box(width="16px"),
                rx.checkbox(
                    checked=VendasState.selecionadas.contains(row["id"]),
                    on_change=lambda _: VendasState.alternar_selecao(row["id"]),
                ),
            )
        ),
        rx.table.cell(rx.text("nº ", row["id"], size="2", color=rx.color("gray", 10))),
        rx.table.cell(row["data_transacao"]),
        rx.table.cell(rx.badge(row["tipo_transacao"], variant="soft")),
        rx.table.cell(row["funcionario_nome"]),
        rx.table.cell(row["cliente_nome"]),
        rx.table.cell(row["qtd_itens"], text_align="center"),
        rx.table.cell(rx.text("R$ ", row["valor_total"]), white_space="nowrap"),
        rx.table.cell(_situacao(row)),
        rx.table.cell(_pagamento(row)),
        rx.table.cell(
            rx.hstack(
                botao_imprimir("venda", row["id"]),
                rx.cond(
                    row["cancelada"],
                    rx.fragment(),
                    _dialogo_cancelar(
                        rx.button(rx.icon("ban", size=14), "Cancelar", size="1", variant="soft",
                                  color_scheme="red", on_click=VendasState.preparar_cancelamento),
                        "Cancelar venda",
                        "A venda continuará no histórico como cancelada, sairá do faturamento e os "
                        "produtos voltarão ao estoque. Uma cobrança em aberto no Asaas também será cancelada.",
                        VendasState.cancelar(row["id"]),
                    ),
                ),
                spacing="2",
            )
        ),
        opacity=rx.cond(row["cancelada"], "0.55", "1"),
    )


# ------------------------------------------------------------------ carrinho

def _linha_carrinho(item: dict, indice: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    item["id_moto"] != "0",
                    rx.badge(rx.icon("bike", size=12), "moto", variant="soft", color_scheme="orange"),
                    rx.cond(item["id_produto"] == "0", rx.badge("avulso", variant="soft", color_scheme="gray")),
                ),
                rx.text(item["descricao"]),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(item["quantidade"], text_align="center"),
        rx.table.cell(rx.text("R$ ", item["valor_unitario"]), white_space="nowrap"),
        rx.table.cell(rx.text("R$ ", item["subtotal"]), white_space="nowrap"),
        rx.table.cell(
            rx.button(rx.icon("x", size=14), size="1", variant="soft", color_scheme="red",
                      on_click=VendasState.remover_item(indice), title="Remover item")
        ),
    )


def _rotulo(texto: str, campo: rx.Component, **props) -> rx.Component:
    return rx.vstack(rx.text(texto, size="1", weight="bold", color=rx.color("gray", 10)), campo,
                     spacing="1", align="start", **props)


def _dado_moto(rotulo: str, valor) -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", color=rx.color("gray", 10)),
        rx.text(rx.cond(valor != "", valor, "—"), size="2", weight="medium"),
        spacing="0",
        align="start",
    )


def _moto_escolhida() -> rx.Component:
    """Foto, preço e dados da moto da loja escolhida, antes de entrar na venda."""
    moto = VendasState.moto_loja
    return rx.card(
        rx.flex(
            rx.cond(
                moto["foto_url"] != "",
                rx.image(src=moto["foto_url"], width="180px", height="120px", object_fit="cover",
                         border_radius="6px"),
                rx.center(rx.icon("bike", size=40, color=rx.color("gray", 8)), width="180px", height="120px"),
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(moto["marca"], " ", moto["modelo"], " ", moto["ano"], size="3"),
                    rx.badge(moto["status"], variant="soft"),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.text("R$ ", moto["preco_venda"], size="5", weight="bold"),
                rx.grid(
                    _dado_moto("Cor", moto["cor"]),
                    _dado_moto("Placa", moto["placa"]),
                    _dado_moto("Chassi", moto["chassi"]),
                    _dado_moto("RENAVAM", moto["renavam"]),
                    _dado_moto("Cilindrada (cm³)", moto["cilindrada"]),
                    _dado_moto("Quilometragem", moto["quilometragem"]),
                    columns=rx.breakpoints(initial="2", sm="3"),
                    spacing="3",
                    width="100%",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            spacing="4",
            width="100%",
        ),
        width="100%",
        variant="surface",
    )


def _forma_de_pagamento() -> rx.Component:
    """Conclusão do pedido: forma de pagamento e, pelo Asaas, o vencimento."""
    return rx.vstack(
        rx.text("Pagamento", size="3", weight="bold"),
        rx.hstack(
            _rotulo("Forma de pagamento", rx.select(VendasState.formas_opcoes, value=VendasState.forma_pagamento,
                                                    on_change=VendasState.set_forma_pagamento, width="100%"),
                    min_width="220px"),
            rx.cond(
                VendasState.cobra_pelo_asaas,
                _rotulo("Vencimento", rx.input(type="date", value=VendasState.vencimento,
                                               on_change=VendasState.set_vencimento, width="170px")),
            ),
            spacing="3",
            align="end",
            wrap="wrap",
            width="100%",
        ),
        rx.cond(
            VendasState.cobra_pelo_asaas,
            rx.text("A cobrança será gerada no Asaas e enviada ao cliente por e-mail e SMS. "
                    "O cliente precisa ter CPF/CNPJ válido e e-mail ou celular no cadastro. "
                    "Os dados do cartão são digitados pelo cliente na página do Asaas.",
                    size="2", color=rx.color("gray", 10)),
            rx.cond(
                ~VendasState.asaas_ligado,
                rx.text("Boleto e cartão pelo Asaas ficam disponíveis quando a chave do Asaas é configurada "
                        "no servidor.", size="1", color=rx.color("gray", 10)),
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Registrar venda", size="4"),
            rx.grid(
                _rotulo("Tipo", rx.select(TIPOS_VENDA, value=VendasState.tipo_transacao,
                                          on_change=VendasState.set_tipo_transacao, width="100%"), width="100%"),
                _rotulo("Funcionário", rx.select(VendasState.funcionarios_opcoes,
                                                 value=VendasState.funcionario_selecionado,
                                                 on_change=VendasState.set_funcionario_selecionado,
                                                 width="100%"), width="100%"),
                _rotulo("Cliente", rx.select(VendasState.clientes_opcoes, value=VendasState.cliente_selecionado,
                                             on_change=VendasState.set_cliente_selecionado, width="100%"),
                        width="100%"),
                _rotulo("Moto do cliente", rx.select(VendasState.motos_opcoes, value=VendasState.moto_selecionada,
                                                     on_change=VendasState.set_moto_selecionada, width="100%",
                                                     disabled=VendasState.tem_moto_no_carrinho),
                        width="100%"),
                columns=rx.breakpoints(initial="1", sm="2", md="4"),
                spacing="3",
                width="100%",
            ),
            rx.divider(),
            rx.text("Itens da venda", size="3", weight="bold"),
            # moto do estoque da loja (preço e dados do cadastro)
            rx.hstack(
                _rotulo("Moto da loja", rx.select(VendasState.motos_loja_opcoes,
                                                  value=VendasState.moto_loja_selecionada,
                                                  on_change=VendasState.definir_moto_loja,
                                                  placeholder="Escolha uma moto do estoque", width="100%"),
                        flex="1", min_width="220px"),
                rx.button(rx.icon("plus", size=16), "Adicionar moto", on_click=VendasState.adicionar_moto,
                          variant="soft", color_scheme="orange"),
                spacing="3",
                align="end",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(VendasState.moto_loja.contains("id"), _moto_escolhida()),
            rx.cond(VendasState.tem_moto_no_carrinho & (VendasState.cliente_selecionado == SEM_CLIENTE),
                    rx.text("Escolha o cliente comprador da moto: ela será cadastrada em Motos dos clientes.",
                            size="2", color=rx.color("orange", 11))),
            # produto do estoque
            rx.hstack(
                _rotulo("Produto", rx.select(VendasState.produtos_opcoes, value=VendasState.produto_selecionado,
                                             on_change=VendasState.definir_produto, placeholder="Escolha um produto",
                                             width="100%"), flex="1", min_width="220px"),
                _rotulo("Qtd.", rx.input(value=VendasState.item_quantidade, on_change=VendasState.set_item_quantidade,
                                         type="number", width="80px")),
                _rotulo("Preço unit. (R$)", rx.input(value=VendasState.item_preco,
                                                     on_change=VendasState.set_item_preco, width="120px")),
                rx.button(rx.icon("plus", size=16), "Adicionar produto", on_click=VendasState.adicionar_produto,
                          variant="soft"),
                spacing="3",
                align="end",
                wrap="wrap",
                width="100%",
            ),
            # item avulso
            rx.hstack(
                _rotulo("Item avulso (sem estoque)", rx.input(placeholder="Ex.: Mão de obra",
                                                              value=VendasState.avulso_descricao,
                                                              on_change=VendasState.set_avulso_descricao,
                                                              width="100%"), flex="1", min_width="220px"),
                _rotulo("Qtd.", rx.input(value=VendasState.avulso_quantidade,
                                         on_change=VendasState.set_avulso_quantidade, type="number", width="80px")),
                _rotulo("Valor unit. (R$)", rx.input(value=VendasState.avulso_valor,
                                                     on_change=VendasState.set_avulso_valor, width="120px")),
                rx.button(rx.icon("plus", size=16), "Adicionar avulso", on_click=VendasState.adicionar_avulso,
                          variant="soft", color_scheme="gray"),
                spacing="3",
                align="end",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                VendasState.carrinho.length() > 0,
                rx.table.root(
                    rx.table.header(rx.table.row(
                        rx.table.column_header_cell("Item"),
                        rx.table.column_header_cell("Qtd.", text_align="center"),
                        rx.table.column_header_cell("Unitário"),
                        rx.table.column_header_cell("Subtotal"),
                        rx.table.column_header_cell(""),
                    )),
                    rx.table.body(rx.foreach(VendasState.carrinho, _linha_carrinho)),
                    width="100%",
                    size="1",
                ),
                rx.text("Nenhum item adicionado.", size="2", color=rx.color("gray", 10)),
            ),
            rx.divider(),
            _forma_de_pagamento(),
            rx.cond(VendasState.erro_venda != "",
                    rx.callout(VendasState.erro_venda, icon="triangle_alert", color_scheme="red", size="1", width="100%")),
            rx.cond(VendasState.sucesso_venda != "",
                    rx.callout(VendasState.sucesso_venda, icon="circle-check", color_scheme="green", size="1",
                               width="100%")),
            rx.hstack(
                rx.button(rx.icon("check", size=16), "Registrar venda", on_click=VendasState.salvar,
                          disabled=VendasState.carrinho.length() == 0),
                rx.button(rx.icon("x", size=16), "Limpar", variant="soft", color_scheme="gray",
                          on_click=VendasState.nova_venda),
                rx.spacer(),
                rx.text("Total: R$ ", VendasState.total_carrinho, size="5", weight="bold"),
                spacing="3",
                align="center",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _barra_lote() -> rx.Component:
    return rx.hstack(
        rx.heading("Últimas vendas", size="4"),
        rx.spacer(),
        rx.cond(
            VendasState.asaas_ligado,
            rx.button(rx.icon("refresh-cw", size=16), "Atualizar pagamentos", size="2", variant="soft",
                      on_click=VendasState.atualizar_pagamentos),
        ),
        rx.cond(
            VendasState.qtd_selecionadas > 0,
            rx.hstack(
                rx.button("Limpar seleção", size="2", variant="ghost", color_scheme="gray",
                          on_click=VendasState.limpar_selecao),
                _dialogo_cancelar(
                    rx.button(rx.icon("ban", size=16), "Cancelar selecionadas (", VendasState.qtd_selecionadas, ")",
                              color_scheme="red", on_click=VendasState.preparar_cancelamento),
                    "Cancelar vendas selecionadas",
                    "As vendas selecionadas continuarão no histórico como canceladas, sairão do faturamento "
                    "e os produtos voltarão ao estoque.",
                    VendasState.cancelar_selecionadas,
                ),
                spacing="3",
                align="center",
            ),
        ),
        width="100%",
        align="center",
    )


def vendas_page() -> rx.Component:
    return page(
        rx.cond(VendasState.aviso_itens != "",
                rx.callout(VendasState.aviso_itens, icon="triangle_alert", color_scheme="amber", width="100%")),
        _formulario(),
        _barra_lote(),
        rx.cond(
            VendasState.resultado_cancelamento.length() > 0,
            rx.callout.root(
                rx.callout.icon(rx.icon("info")),
                rx.vstack(
                    rx.foreach(VendasState.resultado_cancelamento, lambda linha: rx.text(linha, size="2")),
                    rx.button("OK", size="1", variant="soft", on_click=VendasState.fechar_resultado),
                    spacing="1",
                    align="start",
                ),
                color_scheme="blue",
                width="100%",
            ),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(""),
                    rx.table.column_header_cell("Nº"),
                    rx.table.column_header_cell("Data"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Funcionário"),
                    rx.table.column_header_cell("Cliente"),
                    rx.table.column_header_cell("Itens", text_align="center"),
                    rx.table.column_header_cell("Valor"),
                    rx.table.column_header_cell("Situação"),
                    rx.table.column_header_cell("Pagamento"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(VendasState.transacoes, _linha)),
            width="100%",
            variant="surface",
        ),
        title="Vendas / Balcão",
        subtitle="Vendas com vários itens e forma de pagamento; canceladas ficam no histórico e devolvem o estoque.",
    )
