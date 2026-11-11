import reflex as rx

from ..components.layout import page
from ..components.tema import BORDA, LARANJA, LARANJA_SUAVE, PRETO_CARTAO, TEXTO_SECUNDARIO
from ..state.dashboard_state import DashboardState


def _cartao(titulo: str, valor, icone: str, alerta: bool = False, href: str = "") -> rx.Component:
    """Indicador do painel. Todos usam o laranja da marca; só os de alerta
    (ex.: estoque baixo) usam vermelho — sempre com ícone + texto."""
    cor_icone = rx.color("red", 10) if alerta else LARANJA
    fundo_icone = rx.color("red", 3) if alerta else LARANJA_SUAVE
    conteudo = rx.hstack(
        rx.center(
            rx.icon(icone, size=20, color=cor_icone),
            width="42px",
            height="42px",
            flex_shrink="0",
            border_radius="0.6rem",
            background=fundo_icone,
        ),
        rx.vstack(
            rx.text(titulo, size="2", color=TEXTO_SECUNDARIO),
            rx.heading(valor, size="6", color="white"),
            spacing="0",
            align="start",
        ),
        spacing="3",
        align="center",
        padding="1rem",
        background=PRETO_CARTAO,
        border=f"1px solid {BORDA}",
        border_radius="0.75rem",
        width="100%",
        height="100%",
        transition="border-color 0.15s",
        _hover={"border_color": LARANJA} if href else {},
    )
    return rx.link(conteudo, href=href, underline="none", width="100%") if href else conteudo


def _secao(titulo: str, *filhos: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(titulo, size="1", weight="bold", color=LARANJA, letter_spacing="0.15em"),
        *filhos,
        spacing="2",
        width="100%",
        align="start",
    )


def _grafico_faturamento() -> rx.Component:
    return rx.box(
        rx.text("Faturamento por mês — motos + produtos e serviços, últimos 12 meses (R$)", size="3", weight="bold",
                color="white"),
        rx.text(
            "Hoje: R$ ", DashboardState.faturamento_hoje,
            "  ·  Mês: R$ ", DashboardState.faturamento_total_mes,
            "  (motos + produtos e serviços)",
            size="2",
            color=TEXTO_SECUNDARIO,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(vertical=False, stroke=BORDA, stroke_dasharray="3 3"),
            rx.recharts.x_axis(data_key="mes", stroke=TEXTO_SECUNDARIO, tick_line=False, axis_line=False),
            rx.recharts.y_axis(stroke=TEXTO_SECUNDARIO, tick_line=False, axis_line=False, width=70),
            rx.recharts.graphing_tooltip(
                cursor={"fill": "rgba(255,255,255,0.04)"},
                content_style={"background": PRETO_CARTAO, "border": f"1px solid {BORDA}", "borderRadius": "8px"},
                label_style={"color": "white"},
                item_style={"color": "white"},
            ),
            rx.recharts.bar(
                data_key="valor",
                name="Faturamento",
                fill=LARANJA,
                radius=[4, 4, 0, 0],
                max_bar_size=48,
                is_animation_active=False,
            ),
            data=DashboardState.faturamento_12_meses,
            width="100%",
            height=240,
            margin={"top": 16, "right": 8, "left": 0, "bottom": 0},
        ),
        padding="1rem",
        background=PRETO_CARTAO,
        border=f"1px solid {BORDA}",
        border_radius="0.75rem",
        width="100%",
    )


def _linha_atividade(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["data"]),
        rx.table.cell(
            rx.badge(
                row["origem"],
                variant="soft",
                color_scheme=rx.cond(
                    row["origem"] == "Venda", "orange",
                    rx.cond(row["origem"] == "Compra", "gray", "red"),  # "Venda (cancelada)"
                ),
            )
        ),
        rx.table.cell(row["tipo"]),
        rx.table.cell(row["quem"]),
        rx.table.cell(rx.text("R$ ", row["valor"]), text_align="right"),
    )


def dashboard_page() -> rx.Component:
    return page(
        _secao(
            "ESTOQUE",
            rx.grid(
                _cartao("Motos em estoque", DashboardState.motos_em_estoque, "bike", href="/produtos?aba=motos"),
                _cartao("Estoque de Motos (custo)", rx.text("R$ ", DashboardState.valor_estoque_motos), "gem",
                        href="/produtos?aba=motos"),
                _cartao("Vendidas no mês", DashboardState.motos_vendidas_mes, "badge-dollar-sign", href="/produtos?aba=motos"),
                _cartao("Estoque de Produtos", rx.text("R$ ", DashboardState.valor_estoque_produtos), "package-check",
                        href="/produtos"),
                columns=rx.breakpoints(initial="1", sm="2", md="4"),
                spacing="4",
                width="100%",
            ),
        ),
        _secao(
            "FATURAMENTO",
            rx.grid(
                _cartao("Faturamento de hoje", rx.text("R$ ", DashboardState.faturamento_hoje), "wallet", href="/vendas"),
                _cartao("Faturamento de Motos (mês)", rx.text("R$ ", DashboardState.faturamento_motos_mes), "bike",
                        href="/produtos?aba=motos"),
                _cartao("Produtos e serviços (mês)", rx.text("R$ ", DashboardState.faturamento_produtos_mes),
                        "chart-line", href="/vendas"),
                columns=rx.breakpoints(initial="1", sm="3"),
                spacing="4",
                width="100%",
            ),
            _grafico_faturamento(),
        ),
        _secao(
            "LOJA E OFICINA",
            rx.grid(
                _cartao("Produtos cadastrados", DashboardState.total_produtos, "package", href="/produtos"),
                _cartao(
                    "Estoque baixo (≤ 5 un.)",
                    DashboardState.produtos_estoque_baixo,
                    "triangle-alert",
                    alerta=True,
                    href="/produtos",
                ),
                _cartao("Clientes cadastrados", DashboardState.total_clientes, "users", href="/clientes"),
                _cartao("OS em aberto", DashboardState.os_em_aberto, "wrench", href="/ordens-servico"),
                columns=rx.breakpoints(initial="2", md="4"),
                spacing="4",
                width="100%",
            ),
        ),
        _secao(
            "ATIVIDADE RECENTE",
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Data"),
                        rx.table.column_header_cell("Origem"),
                        rx.table.column_header_cell("Tipo"),
                        rx.table.column_header_cell("Quem"),
                        rx.table.column_header_cell("Valor", text_align="right"),
                    )
                ),
                rx.table.body(rx.foreach(DashboardState.atividades_recentes, _linha_atividade)),
                width="100%",
                variant="surface",
            ),
        ),
        title="Painel",
        subtitle="Visão geral da loja, da oficina e do estoque de motos.",
    )
