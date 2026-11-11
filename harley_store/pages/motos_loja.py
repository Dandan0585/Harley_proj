"""
Motos da loja (estoque de motos à venda): formulário, cartões e galeria.
Não é mais uma página própria: aparece na aba "Motos" de Produtos
(pages/produtos.py), que chama `secao_motos()` e `dialogo_foto_moto()`.
"""

import reflex as rx

from ..components.botao_imprimir import botao_imprimir
from ..components.confirm_dialog import confirm_delete_button
from ..components.formulario import mensagem_erro
from ..components.tema import BORDA, LARANJA, PRETO_CARTAO
from ..state.motos_loja_state import MotosLojaState

# Cada status tem cor + ícone + texto (nunca só a cor).
_STATUS_VISUAL = {
    "Em estoque": ("green", "circle-check"),
    "Em preparação": ("cyan", "sparkles"),
    "Em manutenção": ("orange", "wrench"),
    "Reservada": ("amber", "clock"),
    "Consignada": ("blue", "handshake"),
    "Indisponível": ("red", "circle-slash"),
    "Vendida": ("gray", "badge-dollar-sign"),
}


def _badge_status(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        *[
            # "solid" para ficar legível por cima da foto
            (nome, rx.badge(rx.icon(icone, size=12), nome, color_scheme=cor, variant="solid", high_contrast=True))
            for nome, (cor, icone) in _STATUS_VISUAL.items()
        ],
        rx.badge(status, variant="soft"),
    )


def _foto(url: rx.Var, altura: str, descricao: rx.Var | str = "Foto da moto",
          oficial: rx.Var | bool = False) -> rx.Component:
    return rx.cond(
        url != "",
        rx.image(
            src=url,
            alt=descricao,
            loading="lazy",
            width="100%",
            height=altura,
            # foto oficial (perfil de fábrica em fundo branco) aparece inteira
            object_fit=rx.cond(oficial, "contain", "cover"),
            # fundo neutro com ícone se a imagem não carregar (link quebrado, sem internet)
            background=rx.cond(oficial, "white", rx.color("gray", 3)),
            title=rx.cond(oficial, "Foto oficial do modelo (Harley-Davidson)", ""),
        ),
        rx.center(
            rx.icon("bike", size=40, color=rx.color("gray", 8)),
            width="100%",
            height=altura,
            background=rx.color("gray", 3),
        ),
    )


def _cartao_moto(row: dict) -> rx.Component:
    return rx.box(
        rx.box(
            _foto(row["foto_url"], "170px", row["modelo"], row["foto_oficial"]),
            rx.box(_badge_status(row["status"]), position="absolute", top="0.6rem", left="0.6rem"),
            rx.cond(
                row["fotos_urls"].to(list[str]).length() > 1,
                rx.badge(rx.icon("images", size=12), row["fotos_urls"].to(list[str]).length(), variant="solid",
                         color_scheme="gray", high_contrast=True,
                         position="absolute", bottom="0.6rem", right="0.6rem"),
            ),
            rx.cond(
                row["foto_url"] != "",
                rx.icon_button(
                    rx.icon("expand", size=14),
                    size="1",
                    variant="solid",
                    color_scheme="gray",
                    high_contrast=True,
                    position="absolute",
                    top="0.6rem",
                    right="0.6rem",
                    aria_label="Ampliar foto",
                    title="Ampliar foto",
                    on_click=MotosLojaState.ampliar_galeria(row["id"]),
                ),
            ),
            position="relative",
        ),
        rx.vstack(
            rx.text(row["marca"], size="1", color=LARANJA, weight="bold", letter_spacing="0.08em"),
            rx.heading(row["modelo"], size="4"),
            rx.hstack(
                rx.text(row["ano"], size="2", color=rx.color("gray", 10)),
                rx.text("•", size="2", color=rx.color("gray", 8)),
                rx.text(row["cor"], size="2", color=rx.color("gray", 10)),
                rx.text("•", size="2", color=rx.color("gray", 8)),
                rx.text(row["quilometragem"], " km", size="2", color=rx.color("gray", 10)),
                spacing="2",
                wrap="wrap",
            ),
            rx.cond(
                row["localizacao"] != "",
                rx.hstack(rx.icon("map-pin", size=12), rx.text(row["localizacao"], size="1"),
                          spacing="1", align="center", color=rx.color("gray", 10)),
            ),
            rx.hstack(
                rx.text("Placa ", rx.code(row["placa"], variant="ghost"), size="1", color=rx.color("gray", 10)),
                rx.cond(
                    row["cliente_nome"] != "",
                    rx.text("Cliente: ", row["cliente_nome"], size="1", color=rx.color("gray", 10)),
                ),
                spacing="3",
                wrap="wrap",
            ),
            rx.heading(rx.text("R$ ", row["preco_venda"]), size="5", padding_top="0.25rem"),
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    size="1",
                    variant="soft",
                    on_click=MotosLojaState.editar(row["id"]),
                ),
                botao_imprimir(
                    "moto", row["id"],
                    rx.cond(row["status"] == "Vendida", "Recibo", "Ficha"),
                ),
                confirm_delete_button(
                    MotosLojaState.excluir(row["id"]),
                    item_label=f"a moto “{row['modelo']}” ({row['chassi']})",
                ),
                spacing="2",
                padding_top="0.25rem",
            ),
            spacing="1",
            align="start",
            padding="0.9rem 1rem 1rem",
        ),
        background=PRETO_CARTAO,
        border=f"1px solid {BORDA}",
        border_radius="0.75rem",
        overflow="hidden",
        transition="border-color 0.15s, transform 0.15s",
        _hover={"border_color": LARANJA, "transform": "translateY(-2px)"},
    )


def _rotulado(rotulo: str, campo: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="1", weight="bold", color=rx.color("gray", 10)),
        campo,
        spacing="1",
        width="100%",
        align="start",
    )


def _input(rotulo: str, valor, on_change, placeholder: str = "", tipo: str = "text") -> rx.Component:
    return _rotulado(
        rotulo,
        rx.input(value=valor, on_change=on_change, placeholder=placeholder, type=tipo, width="100%"),
    )


def _campo_foto() -> rx.Component:
    return rx.vstack(
        rx.text("Foto da moto", size="1", weight="bold", color=rx.color("gray", 10)),
        rx.hstack(
            rx.box(
                _foto(MotosLojaState.foto_previa, "110px", oficial=MotosLojaState.foto_url == ""),
                width="160px", border_radius="0.6rem", overflow="hidden",
            ),
            rx.vstack(
                rx.upload(
                    rx.hstack(
                        rx.cond(MotosLojaState.enviando_foto, rx.spinner(size="2"), rx.icon("upload", size=16)),
                        rx.text(rx.cond(MotosLojaState.enviando_foto, "Enviando...", "Selecionar foto")),
                        spacing="2",
                        align="center",
                    ),
                    id="upload_foto_moto_loja",
                    accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"], "image/webp": [".webp"]},
                    max_files=1,
                    multiple=False,
                    on_drop=MotosLojaState.handle_upload_foto(rx.upload_files(upload_id="upload_foto_moto_loja")),
                    border=f"1px dashed {rx.color('gray', 7)}",
                    border_radius="0.5rem",
                    padding="0.6rem 0.9rem",
                    cursor="pointer",
                ),
                rx.cond(
                    MotosLojaState.foto_url != "",
                    rx.button(
                        "Remover foto",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=MotosLojaState.remover_foto,
                    ),
                ),
                spacing="2",
                align="start",
            ),
            spacing="4",
            align="center",
            wrap="wrap",
        ),
        rx.cond(
            MotosLojaState.erro_foto != "",
            rx.callout(MotosLojaState.erro_foto, icon="info", color_scheme="amber", size="1"),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _miniatura_extra(url: rx.Var, indice: rx.Var) -> rx.Component:
    return rx.box(
        rx.image(src=url, alt="Foto adicional", width="96px", height="72px", object_fit="cover",
                 border_radius="0.4rem", cursor="zoom-in",
                 on_click=MotosLojaState.ampliar_foto(url, "Foto adicional")),
        rx.hstack(
            rx.icon_button(rx.icon("star", size=12), size="1", variant="soft", title="Tornar principal",
                           aria_label="Tornar principal", on_click=MotosLojaState.definir_principal(indice)),
            rx.icon_button(rx.icon("trash-2", size=12), size="1", variant="soft", color_scheme="red",
                           title="Remover foto", aria_label="Remover foto",
                           on_click=MotosLojaState.remover_foto_extra(indice)),
            spacing="1",
            padding_top="0.25rem",
        ),
    )


def _fotos_extras() -> rx.Component:
    return rx.vstack(
        rx.text("Fotos adicionais (até 8)", size="1", weight="bold", color=rx.color("gray", 10)),
        rx.flex(
            rx.foreach(MotosLojaState.fotos_extras_urls, _miniatura_extra),
            rx.upload(
                rx.vstack(
                    rx.icon("images", size=18),
                    rx.text("Adicionar", size="1"),
                    align="center",
                    spacing="1",
                ),
                id="upload_fotos_extras",
                accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"], "image/webp": [".webp"]},
                max_files=8,
                multiple=True,
                on_drop=MotosLojaState.handle_upload_fotos_extras(rx.upload_files(upload_id="upload_fotos_extras")),
                border=f"1px dashed {rx.color('gray', 7)}",
                border_radius="0.5rem",
                width="96px",
                height="72px",
                display="flex",
                align_items="center",
                justify_content="center",
                cursor="pointer",
            ),
            gap="3",
            wrap="wrap",
        ),
        spacing="2",
        width="100%",
        align="start",
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(MotosLojaState.form_id, "Editar moto", "Nova moto no estoque"), size="4"),
            rx.grid(
                _input("Marca *", MotosLojaState.marca, MotosLojaState.set_marca),
                _input("Modelo *", MotosLojaState.modelo, MotosLojaState.set_modelo, "ex.: Fat Boy 114"),
                _input("Ano", MotosLojaState.ano, MotosLojaState.set_ano, "2026", "number"),
                _input("Cor", MotosLojaState.cor, MotosLojaState.set_cor, "Vivid Black"),
                _input("Placa (se houver)", MotosLojaState.placa, MotosLojaState.set_placa, "ABC1D23"),
                _input("Chassi (obrigatório na venda)", MotosLojaState.chassi, MotosLojaState.set_chassi),
                _input("Quilometragem", MotosLojaState.quilometragem, MotosLojaState.set_quilometragem, "0", "number"),
                _rotulado(
                    "Situação *",
                    rx.select(
                        MotosLojaState.status_opcoes,
                        value=MotosLojaState.status,
                        on_change=MotosLojaState.set_status,
                        width="100%",
                    ),
                ),
                _input("Preço de compra (R$)", MotosLojaState.preco_compra, MotosLojaState.set_preco_compra, "135.000,00"),
                _input("Preço de venda (R$)", MotosLojaState.preco_venda, MotosLojaState.set_preco_venda, "150.000,00"),
                _input("Data de entrada", MotosLojaState.data_entrada, MotosLojaState.set_data_entrada, tipo="date"),
                _input("Data de saída", MotosLojaState.data_saida, MotosLojaState.set_data_saida, tipo="date"),
                _input("RENAVAM", MotosLojaState.renavam, MotosLojaState.set_renavam, "11 dígitos"),
                _input("Cilindrada (cm³)", MotosLojaState.cilindrada, MotosLojaState.set_cilindrada, "1868"),
                _rotulado(
                    "Localização",
                    rx.fragment(
                        rx.input(
                            value=MotosLojaState.localizacao,
                            on_change=MotosLojaState.set_localizacao,
                            placeholder="Showroom, oficina, pátio...",
                            custom_attrs={"list": "lista-localizacoes"},
                            width="100%",
                        ),
                        rx.el.datalist(
                            rx.foreach(MotosLojaState.localizacoes_sugeridas, lambda l: rx.el.option(value=l)),
                            id="lista-localizacoes",
                        ),
                    ),
                ),
                columns=rx.breakpoints(initial="1", sm="2", md="4"),
                spacing="3",
                width="100%",
            ),
            _rotulado(
                "Cliente (comprador / reserva)",
                rx.select(
                    MotosLojaState.clientes_opcoes,
                    value=MotosLojaState.cliente_selecionado,
                    on_change=MotosLojaState.set_cliente_selecionado,
                    width="100%",
                ),
            ),
            _rotulado(
                "Observações",
                rx.text_area(
                    value=MotosLojaState.observacoes,
                    on_change=MotosLojaState.set_observacoes,
                    placeholder="Brindes, revisões feitas, acessórios...",
                    width="100%",
                    rows="2",
                ),
            ),
            _campo_foto(),
            _fotos_extras(),
            mensagem_erro(MotosLojaState.erro_form),
            rx.hstack(
                rx.button(
                    rx.icon("check", size=16),
                    "Salvar",
                    on_click=MotosLojaState.salvar,
                    disabled=MotosLojaState.enviando_foto,
                ),
                rx.button(
                    rx.icon("x", size=16),
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=MotosLojaState.novo,
                ),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        id="form-moto-loja",
        width="100%",
    )


def dialogo_foto_moto() -> rx.Component:
    """Foto em tamanho grande, aberta pelo botão de ampliar do cartão."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(MotosLojaState.foto_ampliada_titulo, size="4"),
            rx.image(
                src=MotosLojaState.foto_ampliada,
                alt=MotosLojaState.foto_ampliada_titulo,
                width="100%",
                max_height="65vh",
                object_fit="contain",
                border_radius="0.5rem",
            ),
            rx.cond(
                MotosLojaState.galeria.length() > 1,
                rx.flex(
                    rx.foreach(
                        MotosLojaState.galeria,
                        lambda url: rx.image(
                            src=url, alt="Miniatura", width="72px", height="54px", object_fit="cover",
                            border_radius="0.3rem", cursor="pointer",
                            border=rx.cond(url == MotosLojaState.foto_ampliada, f"2px solid {LARANJA}", "2px solid transparent"),
                            on_click=MotosLojaState.ver_foto(url),
                        ),
                    ),
                    gap="2",
                    wrap="wrap",
                    padding_top="0.5rem",
                ),
            ),
            rx.flex(
                rx.dialog.close(rx.button("Fechar", variant="soft", color_scheme="gray")),
                justify="end",
                padding_top="0.75rem",
            ),
            max_width="min(960px, 95vw)",
        ),
        open=MotosLojaState.foto_ampliada != "",
        on_open_change=MotosLojaState.fechar_foto,
    )


def secao_motos() -> rx.Component:
    """Aba "Motos" de Produtos: cadastro + busca + cartões das motos da loja."""
    return rx.vstack(
        _formulario(),
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=16)),
                placeholder="Buscar por modelo, placa, chassi, cor ou cliente...",
                value=MotosLojaState.busca,
                on_change=MotosLojaState.definir_busca,
                width="320px",
                max_width="100%",
            ),
            rx.select(
                MotosLojaState.filtros_status,
                value=MotosLojaState.filtro_status,
                on_change=MotosLojaState.definir_filtro_status,
                aria_label="Filtrar por situação",
            ),
            spacing="3",
            wrap="wrap",
            width="100%",
        ),
        rx.cond(
            MotosLojaState.motos.length() == 0,
            rx.center(
                rx.text("Nenhuma moto encontrada.", color=rx.color("gray", 10)),
                width="100%",
                padding="2rem",
            ),
            rx.grid(
                rx.foreach(MotosLojaState.motos, _cartao_moto),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="4",
                width="100%",
            ),
        ),
        align="start",
        width="100%",
        spacing="4",
    )
