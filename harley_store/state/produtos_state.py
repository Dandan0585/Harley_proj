"""State de Produtos (catálogo + estoque). Dados vêm do backend Xano.

Categoria é um texto livre no Xano: a tela sugere as categorias padrão
(CATEGORIAS_PADRAO) e as que já existem nos produtos, e aceita uma nova
digitada, sem precisar mudar código para criar categoria.

A tela mostra as categorias como abas (com a quantidade de produtos de
cada uma) e uma aba "Motos", que é o estoque de motos da loja (tabela
`motos`, state/motos_loja_state.py). Na aba Motos, o formulário e a lista
viram os de moto; nas demais, os de produto. Link direto: /produtos?aba=motos.

Saldo de estoque: a edição manda a VARIAÇÃO digitada pelo funcionário para
`estoque.atualizar_produto`, que a aplica sobre o saldo atual sob a mesma
trava das vendas (ver estoque.py).
"""

import logging
from typing import Optional

import reflex as rx

from .. import estoque
from .. import xano_client as xano
from ..dependencias import em_uso
from ..validacao import inteiro, numero, validar_imagem
from .auth_state import AuthState

log = logging.getLogger("harley_store.produtos")

TABELA = "produtos"

LIMITE_ESTOQUE_BAIXO = 5

# Sem "Motocicletas": motos ficam na aba Motos (tabela própria, com placa,
# chassi, situação...), não como produto.
CATEGORIAS_PADRAO = [
    "Peças", "Vestuário", "Consumíveis", "Acessórios",
    "Motores", "Pneus", "Lubrificantes", "Outros",
]
TODAS = "Todas"
MOTOS = "Motos"

ORIGENS_HISTORICO = {
    "VENDA": "Venda", "CANCELAMENTO_VENDA": "Venda cancelada", "OS": "Ordem de serviço",
    "EXCLUSAO_OS": "OS excluída", "COMPRA": "Compra", "EXCLUSAO_COMPRA": "Compra excluída",
    "AJUSTE": "Ajuste manual", "CADASTRO": "Cadastro do produto",
}

EXTENSOES_IMAGEM_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def _apagar_foto_local(nome_arquivo: str) -> None:
    """Remove uma foto de produto da pasta uploaded_files/ (só nomes gerados pelo app)."""
    if not nome_arquivo or "/" in nome_arquivo or "\\" in nome_arquivo or not nome_arquivo.startswith("produto_"):
        return
    try:
        (rx.get_upload_dir() / nome_arquivo).unlink(missing_ok=True)
    except OSError:
        log.warning("nao foi possivel apagar a foto %s", nome_arquivo)


class ProdutosState(rx.State):
    produtos: list[dict] = []
    categorias: list[str] = []
    # abas: [{"nome": "Peças", "qtd": "12"}, ...] (só categorias com produto, mais as padrão)
    abas_categoria: list[dict] = []
    total_produtos: int = 0
    busca: str = ""
    filtro_categoria: str = TODAS
    somente_estoque_baixo: bool = False

    form_id: Optional[int] = None
    nome_produto: str = ""
    descricao: str = ""
    categoria: str = ""
    estoque_qtd: str = "0"
    preco_venda: str = "0"
    imagem: str = ""
    erro_imagem: str = ""
    enviando_imagem: bool = False
    erro_form: str = ""

    # histórico de movimentações (diálogo)
    historico_produto: str = ""
    historico: list[dict] = []
    historico_aviso: str = ""

    _estoque_lido: int = 0      # saldo quando a edição foi aberta
    _imagem_lida: str = ""      # foto quando a edição foi aberta
    _categoria_lida: str = ""   # categoria quando a edição foi aberta

    @rx.var
    def aba_motos(self) -> bool:
        return self.filtro_categoria == MOTOS

    @rx.event
    async def abrir(self):
        """on_load da página: /produtos?aba=motos abre direto na aba Motos."""
        aba = (self.router.page.params.get("aba") or "").strip().lower()
        if aba == MOTOS.lower():
            self.filtro_categoria = MOTOS
        elif self.filtro_categoria == MOTOS:
            # "Produtos" no menu abre os produtos, mesmo que a última aba vista tenha sido Motos
            self.filtro_categoria = TODAS
        await self.carregar()

    @rx.event
    async def carregar(self):
        todos = await xano.listar(TABELA)
        self.categorias = sorted(
            {*CATEGORIAS_PADRAO, *((r.get("categoria") or "").strip() for r in todos)} - {""},
            key=str.lower,
        )
        contagem: dict[str, int] = {}
        for r in todos:
            nome = (r.get("categoria") or "").strip()
            if nome:
                contagem[nome] = contagem.get(nome, 0) + 1
        self.abas_categoria = [
            {"nome": c, "qtd": str(contagem.get(c, 0))} for c in self.categorias if c.lower() != MOTOS.lower()
        ]
        self.total_produtos = len(todos)
        if self.filtro_categoria not in (TODAS, MOTOS, *self.categorias):
            self.filtro_categoria = TODAS
        registros = todos
        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [
                r for r in registros
                if termo in (r.get("nome_produto") or "").lower() or termo in (r.get("descricao") or "").lower()
            ]
        if self.filtro_categoria not in (TODAS, MOTOS):
            registros = [r for r in registros if (r.get("categoria") or "") == self.filtro_categoria]
        if self.somente_estoque_baixo:
            registros = [r for r in registros if (r.get("estoque_qtd") or 0) <= LIMITE_ESTOQUE_BAIXO]

        registros = sorted(registros, key=lambda r: (r.get("nome_produto") or "").lower())

        self.produtos = [
            {
                "id": str(r["id"]),
                "nome_produto": r.get("nome_produto") or "",
                "descricao": r.get("descricao") or "—",
                "categoria": r.get("categoria") or "—",
                "estoque_qtd": str(r.get("estoque_qtd") or 0),
                "preco_venda": f"{float(r.get('preco_venda') or 0):.2f}",
                "estoque_baixo": (r.get("estoque_qtd") or 0) <= LIMITE_ESTOQUE_BAIXO,
                "imagem": r.get("imagem") or "",
                "imagem_url": xano.url_da_imagem(r.get("imagem")),
            }
            for r in registros
        ]

    @rx.event
    async def definir_busca(self, valor: str):
        self.busca = valor
        await self.carregar()

    @rx.event
    async def definir_filtro_categoria(self, valor: str):
        self.filtro_categoria = valor
        if not self.form_id:
            self.novo()  # novo produto já sai com a categoria da aba
        await self.carregar()

    @rx.event
    async def alternar_filtro_estoque_baixo(self, valor: bool):
        self.somente_estoque_baixo = valor
        await self.carregar()

    @rx.event
    async def abrir_historico(self, produto_id: str, nome: str):
        self.historico_produto, self.historico, self.historico_aviso = nome, [], ""
        try:
            movimentos = await xano.listar(estoque.TABELA_HISTORICO)
        except Exception:
            log.exception("historico de estoque indisponivel")
            self.historico_aviso = "O histórico de estoque ainda não está disponível no servidor de dados."
            return
        pid = int(produto_id)
        do_produto = sorted(
            (m for m in movimentos if int(m.get("produto_id") or 0) == pid),
            key=lambda m: m.get("created_at") or 0, reverse=True,
        )[:100]
        self.historico = [
            {
                "data": xano.epoch_ms_para_datetime(m.get("created_at")).strftime("%d/%m/%Y %H:%M"),
                "origem": ORIGENS_HISTORICO.get(m.get("origem") or "", m.get("origem") or "—"),
                "referencia": f"nº {m['referencia_id']}" if m.get("referencia_id") else "—",
                "quantidade": f"{int(m.get('quantidade') or 0):+d}",
                "entrada": int(m.get("quantidade") or 0) > 0,
                "saldo": str(m.get("saldo_apos") if m.get("saldo_apos") is not None else "—"),
                "usuario": m.get("usuario") or "—",
            }
            for m in do_produto
        ]
        if not self.historico:
            self.historico_aviso = "Nenhuma movimentação registrada para este produto ainda."

    @rx.event
    def fechar_historico(self, aberto: bool = False):
        if not aberto:
            self.historico_produto = ""

    @rx.event
    def novo(self):
        # foto enviada e não salva: não fica esquecida na pasta
        if self.imagem and self.imagem != self._imagem_lida:
            _apagar_foto_local(self.imagem)
        self.form_id = None
        self.nome_produto = ""
        self.descricao = ""
        self.categoria = ""
        self.estoque_qtd = "0"
        self.preco_venda = "0"
        self.imagem = ""
        self.erro_imagem = ""
        self.erro_form = ""
        self._estoque_lido = 0
        self._imagem_lida = ""
        self._categoria_lida = ""
        if self.filtro_categoria not in (TODAS, MOTOS):
            self.categoria = self.filtro_categoria

    @rx.event
    async def editar(self, row: dict):
        # Relê do cache (e não da linha da tela), para o saldo de partida ser o mais recente.
        registro = await xano.buscar(TABELA, int(row["id"]))
        if registro is None:
            await self.carregar()
            return rx.toast.error("Esse produto não existe mais (foi excluído por outra pessoa).")
        self.novo()
        self.form_id = int(registro["id"])
        self.nome_produto = registro.get("nome_produto") or ""
        self.descricao = registro.get("descricao") or ""
        self.categoria = self._categoria_lida = registro.get("categoria") or ""
        self._estoque_lido = int(registro.get("estoque_qtd") or 0)
        self.estoque_qtd = str(self._estoque_lido)
        self.preco_venda = f"{float(registro.get('preco_venda') or 0):.2f}"
        self.imagem = self._imagem_lida = registro.get("imagem") or ""
        return rx.scroll_to("form-produto")

    @rx.event
    async def handle_upload_imagem(self, files: list[rx.UploadFile]):
        """Envia a foto ao armazenamento do Xano e guarda a URL no campo
        `imagem`: a mesma foto aparece na produção e no desenvolvimento.
        (Fotos antigas guardavam só o nome de um arquivo local.)"""
        self.erro_imagem = ""
        if not files:
            return
        arquivo = files[0]
        conteudo = await arquivo.read()
        erro, mime = validar_imagem(arquivo.name or "", conteudo, EXTENSOES_IMAGEM_PERMITIDAS)
        if erro:
            self.erro_imagem = erro
            return
        self.enviando_imagem = True
        yield
        try:
            enviada = await xano.enviar_imagem(arquivo.name or "foto", conteudo, mime)
        except Exception:
            log.exception("falha ao enviar a foto")
            self.erro_imagem = "Não foi possível enviar a foto. Verifique a conexão e tente novamente."
        else:
            self.imagem = enviada.get("url") or ""
        finally:
            self.enviando_imagem = False

    @rx.var
    def imagem_url(self) -> str:
        return xano.url_da_imagem(self.imagem)

    @rx.event
    def remover_imagem(self):
        if self.imagem and self.imagem != self._imagem_lida:
            _apagar_foto_local(self.imagem)
        self.imagem = ""
        self.erro_imagem = ""

    @rx.event
    async def salvar(self):
        self.erro_form = ""
        nome = self.nome_produto.strip()
        categoria = " ".join(self.categoria.split())
        if not nome or not categoria:
            self.erro_form = "Preencha o nome e a categoria do produto."
            return
        if len(nome) > 120:
            self.erro_form = "O nome do produto pode ter no máximo 120 caracteres."
            return
        try:
            estoque_digitado = inteiro(self.estoque_qtd)
            preco = numero(self.preco_venda)
        except ValueError:
            self.erro_form = "O estoque precisa ser um número inteiro e o preço um valor válido (ex.: 149,90)."
            return
        if estoque_digitado < 0 or preco < 0:
            self.erro_form = "Estoque e preço não podem ser negativos."
            return
        if preco > 10_000_000:
            self.erro_form = "Preço acima do limite permitido. Confira o valor digitado."
            return
        # (produto antigo que já estava numa categoria assim continua editável)
        if (categoria.lower() in ("moto", "motos", "motocicleta", "motocicletas")
                and categoria.lower() != self._categoria_lida.lower()):
            self.erro_form = "Motos são cadastradas na aba Motos (com placa, chassi e situação), não como produto."
            return
        # categoria já existente com outra grafia (ex.: "peças" x "Peças")
        categoria = next((c for c in self.categorias if c.lower() == categoria.lower()), categoria)

        duplicado = any(
            (r.get("nome_produto") or "").strip().lower() == nome.lower() and r["id"] != self.form_id
            for r in await xano.listar(TABELA)
        )
        if duplicado:
            self.erro_form = "Já existe um produto com esse nome."
            return

        dados = {
            "nome_produto": nome,
            "descricao": self.descricao.strip() or None,
            "categoria": categoria,
            "preco_venda": round(preco, 2),
            "imagem": self.imagem or None,
        }
        usuario = (await self.get_state(AuthState)).usuario_logado
        if self.form_id is None:
            criado = await xano.criar(TABELA, {**dados, "estoque_qtd": estoque_digitado})
            if estoque_digitado:
                await estoque.registrar_historico(
                    {criado["id"]: estoque_digitado}, {criado["id"]: estoque_digitado}, "CADASTRO", criado["id"], usuario
                )
            mensagem = f"Produto “{nome}” cadastrado."
        else:
            try:
                gravado = await estoque.atualizar_produto(
                    self.form_id, dados, estoque_digitado - self._estoque_lido
                )
            except estoque.ProdutoInexistente:
                self.erro_form = "Esse produto não existe mais (foi excluído por outra pessoa)."
                return
            except estoque.EstoqueInsuficiente:
                self.erro_form = ("O estoque mudou enquanto você editava (houve vendas) e ficaria negativo. "
                                  "Cancele e abra a edição de novo.")
                return
            variacao = estoque_digitado - self._estoque_lido
            if variacao:
                await estoque.registrar_historico(
                    {self.form_id: variacao}, {self.form_id: gravado.get("estoque_qtd")}, "AJUSTE", self.form_id, usuario
                )
            mensagem = f"Produto “{nome}” atualizado."
            if gravado.get("estoque_qtd") != estoque_digitado:
                mensagem += (f" O estoque ficou em {gravado.get('estoque_qtd')}, porque houve "
                             "movimentação enquanto o formulário estava aberto.")
            if self._imagem_lida and self._imagem_lida != self.imagem:
                _apagar_foto_local(self._imagem_lida)

        self._imagem_lida = self.imagem  # a foto agora está salva: novo() não deve apagá-la
        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, produto_id: str):
        pid = int(produto_id)
        usos = await em_uso(TABELA, pid)
        if usos:
            return rx.toast.error(
                f"Este produto não pode ser excluído porque aparece em {', '.join(usos)}. "
                "Para tirá-lo de circulação, deixe o estoque em 0."
            )
        registro = await xano.buscar(TABELA, pid)
        await xano.excluir(TABELA, pid)
        if registro:
            _apagar_foto_local(registro.get("imagem") or "")
        if self.form_id == pid:
            self._imagem_lida = ""
            self.novo()
        await self.carregar()
        return rx.toast.success("Produto excluído.")
