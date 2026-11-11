"""
Página de impressão: /imprimir/[doc_tipo]/[doc_id]  (venda, os, compra, moto).

Desenha o documento montado por ImpressaoState numa "folha" A4 branca.
O botão Imprimir usa a impressão do navegador, que também permite salvar
em PDF. Na impressão, só a folha aparece: barra de botões e fundo somem.
"""

import reflex as rx

from ..components.tema import LARANJA
from ..state.impressao_state import ImpressaoState

_CSS_IMPRESSAO = """
@page { size: A4; margin: 12mm; }
@media print {
  html, body { background: #ffffff !important; }
  .nao-imprimir { display: none !important; }
  .folha { box-shadow: none !important; margin: 0 !important; padding: 0 !important;
           width: auto !important; max-width: none !important; }
  .folha * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  #hs-overlay-carregando { display: none !important; }
}
"""

_TINTA = "#111111"
_CINZA = "#555555"
_LINHA = "#d0d0d0"


def _campo(par: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(par[0], ":", size="1", color=_CINZA, min_width="92px", flex_shrink="0"),
        rx.text(par[1], size="2", color=_TINTA, weight="medium"),
        spacing="2",
        align="baseline",
        width="100%",
    )


def _grupo(titulo: rx.Var, campos: rx.Var) -> rx.Component:
    return rx.cond(
        campos.length() > 0,
        rx.box(
            rx.text(titulo, size="1", weight="bold", color=LARANJA, letter_spacing="0.12em",
                    text_transform="uppercase", padding_bottom="0.35rem"),
            rx.vstack(rx.foreach(campos, _campo), spacing="1", width="100%"),
            border=f"1px solid {_LINHA}",
            border_radius="6px",
            padding="0.7rem 0.85rem",
            width="100%",
            style={"breakInside": "avoid"},
        ),
    )


def _celula(texto: rx.Var, indice: int) -> rx.Component:
    # a primeira coluna (descrição) alinha à esquerda; as demais (números), à direita
    return rx.el.td(
        texto,
        style={"padding": "6px 8px", "borderBottom": f"1px solid {_LINHA}", "color": _TINTA,
               "fontSize": "13px", "textAlign": rx.cond(indice == 0, "left", "right")},
    )


def _cabecalho_coluna(texto: rx.Var, indice: int) -> rx.Component:
    return rx.el.th(
        texto,
        style={"padding": "6px 8px", "background": "#f2f2f2", "color": _TINTA, "fontSize": "12px",
               "textAlign": rx.cond(indice == 0, "left", "right"), "borderBottom": f"2px solid {_TINTA}"},
    )


def _tabela_itens() -> rx.Component:
    return rx.cond(
        ImpressaoState.itens_cabecalho.length() > 0,
        rx.vstack(
            rx.text(ImpressaoState.itens_titulo, size="1", weight="bold", color=LARANJA,
                    letter_spacing="0.12em", text_transform="uppercase"),
            rx.el.table(
                rx.el.thead(rx.el.tr(rx.foreach(ImpressaoState.itens_cabecalho, _cabecalho_coluna))),
                rx.el.tbody(
                    rx.foreach(
                        ImpressaoState.itens,
                        lambda linha: rx.el.tr(rx.foreach(linha, _celula)),
                    )
                ),
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
            rx.hstack(
                rx.spacer(),
                rx.box(
                    rx.hstack(
                        rx.text(ImpressaoState.total_rotulo, size="2", weight="bold", color="#ffffff"),
                        rx.text(ImpressaoState.total, size="4", weight="bold", color="#ffffff"),
                        spacing="4",
                        align="center",
                    ),
                    background=_TINTA,
                    border_left=f"5px solid {LARANJA}",
                    padding="0.45rem 0.9rem",
                    border_radius="4px",
                ),
                width="100%",
            ),
            spacing="2",
            width="100%",
            style={"breakInside": "avoid"},
        ),
    )


def _assinatura(nome: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.box(height="2.6rem"),
        rx.box(border_top=f"1px solid {_TINTA}", width="100%"),
        rx.text(nome, size="1", color=_CINZA),
        align="center",
        spacing="1",
        flex="1",
    )


def _cabecalho() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("HARLEY STORE", size="6", weight="bold", color=_TINTA, letter_spacing="0.08em"),
            rx.text("Loja e Oficina Harley-Davidson", size="2", color=_CINZA),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text(ImpressaoState.titulo, size="3", weight="bold", color=_TINTA, text_align="right"),
            rx.text(ImpressaoState.numero, size="4", weight="bold", color=LARANJA),
            rx.text("Emitido em ", ImpressaoState.emitido_em, size="1", color=_CINZA),
            spacing="0",
            align="end",
        ),
        width="100%",
        align="center",
        padding_bottom="0.6rem",
        border_bottom=f"4px solid {LARANJA}",
    )


def _folha() -> rx.Component:
    return rx.box(
        rx.vstack(
            _cabecalho(),
            rx.cond(
                ImpressaoState.faixa != "",
                rx.box(
                    rx.text(ImpressaoState.faixa, size="3", weight="bold", color="#b00020", text_align="center"),
                    border="3px solid #b00020",
                    border_radius="6px",
                    padding="0.6rem",
                    width="100%",
                ),
            ),
            rx.grid(
                _grupo(ImpressaoState.grupo1_titulo, ImpressaoState.grupo1),
                _grupo(ImpressaoState.grupo2_titulo, ImpressaoState.grupo2),
                columns="2",
                spacing="3",
                width="100%",
            ),
            _grupo(ImpressaoState.grupo3_titulo, ImpressaoState.grupo3),
            _tabela_itens(),
            rx.cond(
                ImpressaoState.observacoes != "",
                rx.box(
                    rx.text("Observações: ", ImpressaoState.observacoes, size="2", color=_TINTA),
                    border=f"1px dashed {_LINHA}",
                    padding="0.6rem 0.8rem",
                    border_radius="6px",
                    width="100%",
                ),
            ),
            rx.cond(
                ImpressaoState.termo != "",
                rx.text(ImpressaoState.termo, size="1", color=_CINZA, text_align="justify"),
            ),
            rx.hstack(rx.foreach(ImpressaoState.assinaturas, _assinatura), spacing="8",
                      width="100%", padding_top="1.2rem"),
            rx.text("Documento gerado pelo sistema Harley Store.", size="1", color="#999999",
                    align_self="center", padding_top="0.8rem"),
            spacing="4",
            width="100%",
        ),
        class_name="folha",
        background="#ffffff",
        width="210mm",
        max_width="100%",
        min_height="297mm",
        padding="14mm",
        margin="1rem auto 2rem",
        box_shadow="0 4px 28px rgba(0,0,0,0.35)",
    )


def _barra() -> rx.Component:
    return rx.hstack(
        rx.button(rx.icon("printer", size=16), "Imprimir / salvar PDF",
                  on_click=rx.call_script("window.print()"), size="3",
                  disabled=ImpressaoState.carregando | (ImpressaoState.erro != "")),
        rx.button(rx.icon("x", size=16), "Fechar", on_click=rx.call_script("window.close()"),
                  variant="soft", color_scheme="gray", size="3"),
        class_name="nao-imprimir",
        justify="center",
        spacing="3",
        padding="1rem",
        width="100%",
    )


def impressao_page() -> rx.Component:
    return rx.theme(
        rx.el.style(_CSS_IMPRESSAO),
        rx.box(
            _barra(),
            rx.cond(
                ImpressaoState.carregando,
                rx.center(rx.spinner(size="3"), rx.text("Carregando documento...", color="#bbbbbb"),
                          spacing="3", padding="4rem", class_name="nao-imprimir"),
                rx.cond(
                    ImpressaoState.erro != "",
                    rx.center(rx.callout(ImpressaoState.erro, icon="triangle_alert", color_scheme="red"),
                              padding="4rem"),
                    _folha(),
                ),
            ),
            background="#3a3a3a",
            min_height="100vh",
            padding_x="0.5rem",
        ),
        appearance="light",
        accent_color="orange",
        has_background=False,
    )
