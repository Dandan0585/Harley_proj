"""
State de Motos dos Clientes.

Este arquivo mostra o padrão a seguir sempre que uma tabela nova
referenciar outra (chave estrangeira): além da lista principal, o state
também carrega uma lista de opções (`clientes_opcoes`) para alimentar o
`rx.select` do formulário, e faz um JOIN simples (em Python) para mostrar
o nome do cliente na tabela em vez do id_cliente cru. Dados vêm do
backend Xano.
"""

import asyncio
import logging
import re
from typing import Optional

import reflex as rx

from .. import xano_client as xano
from ..fotos_oficiais import foto_oficial
from ..dependencias import em_uso, mensagem_em_uso
from ..validacao import validar_imagem

log = logging.getLogger("harley_store.motos_clientes")

TABELA = "motos_clientes"
TABELA_CLIENTES = "clientes"

EXTENSOES_IMAGEM_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# Placa antiga (ABC1234) ou Mercosul (ABC1D23), sem hífen.
_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


def normalizar_placa(placa: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (placa or "").upper())


def _apagar_foto_local(nome_arquivo: str) -> None:
    if not nome_arquivo or "/" in nome_arquivo or "\\" in nome_arquivo or not nome_arquivo.startswith("moto_"):
        return
    try:
        (rx.get_upload_dir() / nome_arquivo).unlink(missing_ok=True)
    except OSError:
        log.warning("nao foi possivel apagar a foto %s", nome_arquivo)


class MotosState(rx.State):
    motos: list[dict] = []
    busca: str = ""

    clientes_opcoes: list[str] = []  # ex.: ["3 - João Pereira", ...]

    form_id: Optional[int] = None
    cliente_selecionado: str = ""
    modelo: str = ""
    placa: str = ""
    chassi: str = ""
    imagem: str = ""
    erro_imagem: str = ""
    enviando_imagem: bool = False
    erro_form: str = ""

    _imagem_lida: str = ""

    @rx.event
    async def carregar(self):
        clientes, registros = await asyncio.gather(xano.listar(TABELA_CLIENTES), xano.listar(TABELA))
        clientes.sort(key=lambda c: (c.get("nome_cliente") or "").lower())
        self.clientes_opcoes = [f"{c['id']} - {c['nome_cliente']}" for c in clientes]
        nomes_por_id = {c["id"]: c["nome_cliente"] for c in clientes}

        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [
                r for r in registros
                if termo in (r.get("modelo") or "").lower()
                or normalizar_placa(termo) and normalizar_placa(termo).lower() in (r.get("placa") or "").lower().replace("-", "")
                or termo in (r.get("chassi") or "").lower()
                or termo in (nomes_por_id.get(r.get("id_cliente")) or "").lower()
            ]
        registros = sorted(registros, key=lambda r: (r.get("modelo") or "").lower())

        self.motos = [
            {
                "id": str(r["id"]),
                "modelo": r.get("modelo") or "",
                "placa": r.get("placa") or "",
                "chassi": r.get("chassi") or "",
                "id_cliente": str(r.get("id_cliente") or 0),
                "cliente_nome": nomes_por_id.get(r.get("id_cliente"), "(cliente removido)"),
                "imagem": r.get("imagem") or "",
                # foto enviada pela loja; sem ela, a foto oficial do modelo cadastrado
                "imagem_url": xano.url_da_imagem(r.get("imagem")) or foto_oficial(r.get("modelo") or ""),
                "foto_oficial": not r.get("imagem") and bool(foto_oficial(r.get("modelo") or "")),
            }
            for r in registros
        ]

    @rx.event
    async def definir_busca(self, valor: str):
        self.busca = valor
        await self.carregar()

    @rx.event
    def novo(self):
        if self.imagem and self.imagem != self._imagem_lida:
            _apagar_foto_local(self.imagem)  # foto enviada e não salva
        self.form_id = None
        self.cliente_selecionado = ""
        self.modelo = ""
        self.placa = ""
        self.chassi = ""
        self.imagem = ""
        self.erro_imagem = ""
        self.erro_form = ""
        self._imagem_lida = ""

    @rx.event
    def editar(self, row: dict):
        self.novo()
        self.form_id = int(row["id"])
        opcao = f"{row['id_cliente']} - {row['cliente_nome']}"
        self.cliente_selecionado = opcao if opcao in self.clientes_opcoes else ""
        self.modelo = row["modelo"]
        self.placa = row["placa"]
        self.chassi = row["chassi"]
        self.imagem = self._imagem_lida = row.get("imagem") or ""
        return rx.scroll_to("form-moto-cliente")

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
        modelo = " ".join(self.modelo.split())
        placa = normalizar_placa(self.placa)
        chassi = re.sub(r"\s", "", self.chassi).upper()
        if not self.cliente_selecionado:
            # Antes, sem cliente escolhido, a moto era gravada em nome do
            # primeiro cliente da lista (dono errado, sem aviso).
            self.erro_form = "Escolha o cliente dono da moto."
            return
        if self.cliente_selecionado not in self.clientes_opcoes:
            self.erro_form = "O cliente escolhido não existe mais. Escolha de novo."
            return
        if not modelo or not placa or not chassi:
            self.erro_form = "Preencha modelo, placa e chassi."
            return
        if not _PLACA.match(placa):
            self.erro_form = "Placa inválida. Use o formato ABC1234 ou Mercosul ABC1D23."
            return
        if not re.fullmatch(r"[A-Z0-9]{6,17}", chassi):
            self.erro_form = "Chassi inválido: use só letras e números (até 17 caracteres)."
            return

        id_cliente = int(self.cliente_selecionado.split(" - ")[0])

        duplicado = next(
            (r for r in await xano.listar(TABELA)
             if (normalizar_placa(r.get("placa")) == placa or (r.get("chassi") or "").upper() == chassi)
             and r["id"] != self.form_id),
            None,
        )
        if duplicado:
            self.erro_form = f"Já existe uma moto cadastrada com essa placa ou chassi ({duplicado.get('modelo')})."
            return

        dados = {
            "id_cliente": id_cliente,
            "modelo": modelo,
            "placa": placa,
            "chassi": chassi,
            "imagem": self.imagem or None,
        }
        if self.form_id is None:
            await xano.criar(TABELA, dados)
            mensagem = "Moto cadastrada."
        else:
            await xano.atualizar(TABELA, self.form_id, dados)
            mensagem = "Moto atualizada."
            if self._imagem_lida and self._imagem_lida != self.imagem:
                _apagar_foto_local(self._imagem_lida)

        self._imagem_lida = self.imagem
        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, moto_id: str):
        usos = await em_uso(TABELA, int(moto_id))
        if usos:
            return rx.toast.error(mensagem_em_uso("esta moto", usos))
        registro = await xano.buscar(TABELA, int(moto_id))
        await xano.excluir(TABELA, int(moto_id))
        if registro:
            _apagar_foto_local(registro.get("imagem") or "")
        if self.form_id == int(moto_id):
            self._imagem_lida = ""
            self.novo()
        await self.carregar()
        return rx.toast.success("Moto excluída.")
