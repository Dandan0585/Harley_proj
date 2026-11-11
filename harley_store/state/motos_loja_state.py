"""
State de Motos da Loja (estoque de motos à venda) — tabela `motos` do Xano.
A tela fica na aba "Motos" de Produtos (pages/produtos.py).

Não confundir com `motos_state.py` (motos dos CLIENTES, que passam pela
oficina). Aqui ficam as motos que a loja compra e revende.

Dois cuidados específicos desta tabela no Xano:

- O PATCH gerado pelo Xano SUBSTITUI o registro inteiro: campo que não
  for enviado volta zerado/vazio (inclusive a foto). Por isso `salvar()`
  sempre manda todos os campos, e guarda o objeto da foto já existente em
  `_foto` para reenviá-lo sem mudanças quando o usuário não troca a foto.
- `foto` é um campo de imagem do Xano (objeto com path/url), não um nome
  de arquivo local. Foto nova passa por `xano.enviar_imagem`.
- Datas (`data_entrada`/`data_saida`) são epoch em ms; 0 = sem data.

Moto sem foto enviada mostra a foto oficial do modelo (fotos_oficiais.py).
O chassi pode ficar vazio enquanto a unidade não chegou, mas é exigido para
marcar a moto como Vendida (vai no recibo). Ao vender para um cliente com
e-mail, ele recebe um e-mail de parabéns (email_clientes.py).
"""

import asyncio
import datetime
import logging
import re
from typing import Optional

import reflex as rx

from .. import email_clientes
from .. import xano_client as xano
from ..dependencias import em_uso, mensagem_em_uso
from ..fotos_oficiais import foto_oficial
from ..validacao import inteiro, numero, validar_imagem

log = logging.getLogger("harley_store.motos_loja")

TABELA = "motos"
TABELA_CLIENTES = "clientes"

# Situações da moto. "Em estoque" é a moto disponível para venda (nome
# mantido porque já está gravado nos registros). O campo no Xano é texto
# livre: para criar uma situação nova basta acrescentá-la aqui e em
# pages/motos_loja.py (_STATUS_VISUAL). Só "Vendida" tira a moto do estoque.
STATUS_OPCOES = [
    "Em estoque", "Em preparação", "Em manutenção", "Reservada", "Consignada", "Indisponível", "Vendida",
]
STATUS_FORA_DO_ESTOQUE = {"Vendida"}
SEM_CLIENTE = "— nenhum —"

EXTENSOES_IMAGEM_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp"}

LOCALIZACOES_SUGERIDAS = ["Showroom", "Oficina", "Pátio", "Preparação", "Outra loja", "Com o cliente"]
MAX_FOTOS_EXTRAS = 8

# Placa antiga (ABC1234) ou Mercosul (ABC1D23), sem hífen; moto 0 km pode não ter.
_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


def _moeda(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data_para_input(epoch_ms: int | None) -> str:
    return xano.epoch_ms_para_datetime(epoch_ms).strftime("%Y-%m-%d") if epoch_ms else ""


def _input_para_epoch(texto: str) -> int:
    if not texto:
        return 0
    return xano.datetime_para_epoch_ms(datetime.datetime.strptime(texto, "%Y-%m-%d"))


def _linha_moto(r: dict, nomes_por_id: dict) -> dict:
    """Registro da tabela motos -> linha (cartão) da tela."""
    enviada = ((r.get("foto") or {}).get("url")) or ""
    oficial = foto_oficial(r.get("modelo") or "")
    principal = enviada or oficial
    return {
        "id": str(r["id"]),
        "marca": r.get("marca") or "",
        "modelo": r.get("modelo") or "",
        "ano": str(r.get("ano") or ""),
        "cor": r.get("cor") or "",
        "placa": r.get("placa") or "",
        "chassi": r.get("chassi") or "",
        "quilometragem": str(r.get("quilometragem") or 0),
        "status": r.get("status") or "Em estoque",
        "preco_compra": _moeda(r.get("preco_compra") or 0),
        "preco_venda": _moeda(r.get("preco_venda") or 0),
        "data_entrada": _data_para_input(r.get("data_entrada")),
        "data_saida": _data_para_input(r.get("data_saida")),
        "observacoes": r.get("observacoes") or "",
        "id_cliente": str(r.get("cliente_id") or 0),
        "cliente_nome": nomes_por_id.get(r.get("cliente_id"), ""),
        # foto enviada pela loja; sem ela, a foto oficial do modelo
        "foto_url": principal,
        "foto_oficial": not enviada and bool(oficial),
        "fotos_urls": [u for u in [principal]
                       + [(f or {}).get("url") or "" for f in (r.get("fotos") or []) if isinstance(f, dict)] if u],
        "renavam": r.get("renavam") or "",
        "cilindrada": str(r.get("cilindrada") or ""),
        "localizacao": r.get("localizacao") or "",
    }


class MotosLojaState(rx.State):
    motos: list[dict] = []
    total_motos: int = 0  # todas as motos cadastradas (contador da aba Motos)
    busca: str = ""
    filtro_status: str = "Todos"

    clientes_opcoes: list[str] = []

    form_id: Optional[int] = None
    marca: str = "Harley-Davidson"
    modelo: str = ""
    ano: str = ""
    cor: str = ""
    placa: str = ""
    chassi: str = ""
    quilometragem: str = ""
    status: str = "Em estoque"
    preco_compra: str = ""
    preco_venda: str = ""
    data_entrada: str = ""
    data_saida: str = ""
    observacoes: str = ""
    cliente_selecionado: str = SEM_CLIENTE
    renavam: str = ""
    cilindrada: str = ""
    localizacao: str = ""

    foto_url: str = ""
    # fotos adicionais: objetos de imagem do Xano (a principal fica em _foto)
    _fotos_extras: list[dict] = []
    fotos_extras_urls: list[str] = []
    erro_foto: str = ""
    enviando_foto: bool = False
    _foto: dict = {}

    erro_form: str = ""
    # situação e cliente quando a edição foi aberta (para saber se a venda é nova)
    _status_lido: str = ""
    _cliente_lido: int = 0
    # foto aberta em tamanho grande (diálogo); "" = fechado
    foto_ampliada: str = ""
    foto_ampliada_titulo: str = ""
    galeria: list[str] = []

    @rx.var
    def localizacoes_sugeridas(self) -> list[str]:
        return LOCALIZACOES_SUGERIDAS

    @rx.var
    def status_opcoes(self) -> list[str]:
        return STATUS_OPCOES

    @rx.var
    def filtros_status(self) -> list[str]:
        return ["Todos", *STATUS_OPCOES]

    @rx.var
    def foto_previa(self) -> str:
        """Foto mostrada no formulário: a enviada ou, sem ela, a oficial do modelo digitado."""
        return self.foto_url or foto_oficial(self.modelo)

    @rx.event
    async def carregar(self):
        clientes, registros = await asyncio.gather(xano.listar(TABELA_CLIENTES), xano.listar(TABELA))
        clientes.sort(key=lambda c: c["nome_cliente"])
        self.clientes_opcoes = [SEM_CLIENTE, *[f"{c['id']} - {c['nome_cliente']}" for c in clientes]]
        nomes_por_id = {c["id"]: c["nome_cliente"] for c in clientes}
        self.total_motos = len(registros)

        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [
                r for r in registros
                if termo in " ".join(str(r.get(c) or "") for c in ("marca", "modelo", "placa", "chassi", "cor", "ano")).lower()
                or termo in (nomes_por_id.get(r.get("cliente_id")) or "").lower()
            ]
        if self.filtro_status != "Todos":
            registros = [r for r in registros if r.get("status") == self.filtro_status]
        registros.sort(key=lambda r: ((r.get("marca") or "").lower(), (r.get("modelo") or "").lower(), r.get("ano") or 0))

        self.motos = [_linha_moto(r, nomes_por_id) for r in registros]


    @rx.event
    async def definir_busca(self, valor: str):
        self.busca = valor
        await self.carregar()

    @rx.event
    async def definir_filtro_status(self, valor: str | list[str]):
        # o segmented_control declara str | list[str]; aqui é sempre um só valor
        self.filtro_status = valor[0] if isinstance(valor, list) else valor
        await self.carregar()

    @rx.event
    def ampliar_foto(self, url: str, titulo: str):
        self.foto_ampliada = url
        self.foto_ampliada_titulo = titulo
        self.galeria = [url]

    @rx.event
    def ampliar_galeria(self, moto_id: str):
        """Abre todas as fotos da moto (principal primeiro)."""
        moto = next((m for m in self.motos if m["id"] == moto_id), None)
        if moto and moto["fotos_urls"]:
            self.galeria = list(moto["fotos_urls"])
            self.foto_ampliada = self.galeria[0]
            self.foto_ampliada_titulo = f"{moto['marca']} {moto['modelo']}"

    @rx.event
    def ver_foto(self, url: str):
        self.foto_ampliada = url

    @rx.event
    def fechar_foto(self, aberto: bool = False):
        if not aberto:
            self.foto_ampliada = ""

    @rx.event
    def novo(self):
        self.erro_form = ""
        self.form_id = None
        self.marca = "Harley-Davidson"
        self.modelo = ""
        self.ano = ""
        self.cor = ""
        self.placa = ""
        self.chassi = ""
        self.quilometragem = ""
        self.status = "Em estoque"
        self.preco_compra = ""
        self.preco_venda = ""
        self.data_entrada = datetime.date.today().strftime("%Y-%m-%d")
        self.data_saida = ""
        self.observacoes = ""
        self.cliente_selecionado = SEM_CLIENTE
        self.foto_url = ""
        self.erro_foto = ""
        self._foto = {}
        self._fotos_extras = []
        self.fotos_extras_urls = []
        self.renavam = ""
        self.cilindrada = ""
        self.localizacao = "Showroom"
        self._status_lido = ""
        self._cliente_lido = 0

    @rx.event
    async def editar(self, moto_id: str):
        registro = await xano.buscar(TABELA, int(moto_id))
        if registro is None:
            await self.carregar()
            return rx.toast.error("Essa moto não existe mais (foi excluída por outra pessoa).")
        self.erro_form = ""
        self.form_id = registro["id"]
        self.marca = registro.get("marca") or ""
        self.modelo = registro.get("modelo") or ""
        self.ano = str(registro.get("ano") or "")
        self.cor = registro.get("cor") or ""
        self.placa = registro.get("placa") or ""
        self.chassi = registro.get("chassi") or ""
        self.quilometragem = str(registro.get("quilometragem") or "")
        self.status = registro.get("status") or "Em estoque"
        self.preco_compra = _moeda(registro.get("preco_compra") or 0)
        self.preco_venda = _moeda(registro.get("preco_venda") or 0)
        self.data_entrada = _data_para_input(registro.get("data_entrada"))
        self.data_saida = _data_para_input(registro.get("data_saida"))
        self.observacoes = registro.get("observacoes") or ""
        cliente_id = registro.get("cliente_id") or 0
        self.cliente_selecionado = next(
            (op for op in self.clientes_opcoes if op.startswith(f"{cliente_id} - ")), SEM_CLIENTE
        )
        foto = registro.get("foto") or {}
        self._foto = foto if foto.get("path") else {}
        self.foto_url = foto.get("url") or ""
        self._fotos_extras = [f for f in (registro.get("fotos") or []) if isinstance(f, dict) and f.get("url")]
        self.fotos_extras_urls = [f["url"] for f in self._fotos_extras]
        self.renavam = registro.get("renavam") or ""
        self.cilindrada = str(registro.get("cilindrada") or "")
        self.localizacao = registro.get("localizacao") or ""
        self._status_lido = self.status
        self._cliente_lido = int(cliente_id or 0)
        self.erro_foto = ""
        return rx.scroll_to("form-moto-loja")

    @rx.event
    async def handle_upload_foto(self, files: list[rx.UploadFile]):
        self.erro_foto = ""
        if not files:
            return
        arquivo = files[0]
        conteudo = await arquivo.read()
        erro, mime = validar_imagem(arquivo.name or "", conteudo, EXTENSOES_IMAGEM_PERMITIDAS)
        if erro:
            self.erro_foto = erro
            return
        self.enviando_foto = True
        yield
        try:
            imagem = await xano.enviar_imagem(arquivo.name, conteudo, mime)
        except xano.UploadIndisponivel:
            self.erro_foto = (
                "O Xano ainda não tem o endpoint motos/foto: rode scripts\\aplicar_xano.ps1. "
                "A moto pode ser salva sem foto."
            )
        except Exception:
            log.exception("falha ao enviar a foto da moto")
            self.erro_foto = "Não foi possível enviar a foto. Verifique a conexão e tente novamente."
        else:
            self._foto = imagem
            self.foto_url = imagem.get("url") or ""
        finally:
            self.enviando_foto = False

    @rx.event
    async def handle_upload_fotos_extras(self, files: list[rx.UploadFile]):
        """Fotos adicionais (até MAX_FOTOS_EXTRAS), enviadas ao Xano uma a uma."""
        self.erro_foto = ""
        vagas = MAX_FOTOS_EXTRAS - len(self._fotos_extras)
        if not files:
            return
        if vagas <= 0:
            self.erro_foto = f"Limite de {MAX_FOTOS_EXTRAS} fotos adicionais atingido."
            return
        self.enviando_foto = True
        yield
        try:
            for arquivo in files[:vagas]:
                conteudo = await arquivo.read()
                erro, mime = validar_imagem(arquivo.name or "", conteudo, EXTENSOES_IMAGEM_PERMITIDAS)
                if erro:
                    self.erro_foto = f"{arquivo.name}: {erro}"
                    continue
                try:
                    imagem = await xano.enviar_imagem(arquivo.name or "foto", conteudo, mime)
                except Exception:
                    log.exception("falha ao enviar foto adicional")
                    self.erro_foto = "Algumas fotos não puderam ser enviadas. Tente novamente."
                    continue
                self._fotos_extras = [*self._fotos_extras, imagem]
                self.fotos_extras_urls = [f.get("url") or "" for f in self._fotos_extras]
                yield
            if len(files) > vagas:
                self.erro_foto = f"Só {MAX_FOTOS_EXTRAS} fotos adicionais por moto: as excedentes foram ignoradas."
        finally:
            self.enviando_foto = False

    @rx.event
    def remover_foto_extra(self, indice: int):
        self._fotos_extras = [f for i, f in enumerate(self._fotos_extras) if i != indice]
        self.fotos_extras_urls = [f.get("url") or "" for f in self._fotos_extras]

    @rx.event
    def definir_principal(self, indice: int):
        """A foto adicional escolhida vira a principal (a principal atual vai para as adicionais)."""
        if not 0 <= indice < len(self._fotos_extras):
            return
        extras = list(self._fotos_extras)
        nova_principal = extras.pop(indice)
        if self._foto:
            extras.insert(0, self._foto)
        self._foto, self._fotos_extras = nova_principal, extras
        self.foto_url = nova_principal.get("url") or ""
        self.fotos_extras_urls = [f.get("url") or "" for f in extras]

    @rx.event
    def remover_foto(self):
        self._foto = {}
        self.foto_url = ""
        self.erro_foto = ""

    def _validar(self) -> str:
        if self.status not in STATUS_OPCOES:
            return "Escolha uma situação válida."
        if not self.marca.strip() or not self.modelo.strip():
            return "Preencha marca e modelo."
        placa = re.sub(r"[^A-Z0-9]", "", self.placa.upper())
        if placa and not _PLACA.match(placa):
            return "Placa inválida. Use o formato ABC1234 ou Mercosul ABC1D23 (ou deixe vazio se a moto não tem placa)."
        chassi = re.sub(r"\s", "", self.chassi).upper()
        if chassi and not re.fullmatch(r"[A-Z0-9]{6,17}", chassi):
            return "Chassi inválido: use só letras e números (até 17 caracteres)."
        if self.status == "Vendida" and not chassi:
            return "Para marcar como Vendida, informe o chassi (ele aparece no recibo)."
        try:
            ano = inteiro(self.ano)
            km = inteiro(self.quilometragem)
            preco_compra = numero(self.preco_compra)
            preco_venda = numero(self.preco_venda)
        except ValueError:
            return "Ano e quilometragem precisam ser números inteiros, e os preços valores válidos (ex.: 150.000,00)."
        if ano and not 1903 <= ano <= datetime.date.today().year + 1:
            return "Ano inválido."
        if not 0 <= km <= 2_000_000:
            return "Quilometragem inválida."
        if preco_compra < 0 or preco_venda < 0 or max(preco_compra, preco_venda) > 100_000_000:
            return "Preços não podem ser negativos nem exagerados. Confira os valores."
        renavam = re.sub(r"\D", "", self.renavam)
        if renavam and len(renavam) != 11:
            return "RENAVAM inválido: são 11 dígitos (ou deixe vazio se ainda não houver)."
        try:
            cilindrada = inteiro(self.cilindrada)
        except ValueError:
            return "A cilindrada precisa ser um número inteiro (cm³), por exemplo 1868."
        if cilindrada and not 50 <= cilindrada <= 3000:
            return "Cilindrada fora do esperado (50 a 3000 cm³)."
        if self.data_entrada and self.data_saida and self.data_saida < self.data_entrada:
            return "A data de saída não pode ser anterior à data de entrada."
        if self.status == "Vendida" and self.cliente_selecionado == SEM_CLIENTE:
            return "Para marcar como Vendida, escolha o cliente comprador (ele aparece no recibo)."
        if self.cliente_selecionado != SEM_CLIENTE and self.cliente_selecionado not in self.clientes_opcoes:
            return "O cliente escolhido não existe mais. Escolha de novo."
        return ""

    @rx.event
    async def salvar(self):
        self.erro_form = self._validar()
        if self.erro_form:
            return
        modelo = " ".join(self.modelo.split())
        placa = re.sub(r"[^A-Z0-9]", "", self.placa.upper())
        chassi = re.sub(r"\s", "", self.chassi).upper()
        ano = inteiro(self.ano)
        quilometragem = inteiro(self.quilometragem)
        preco_compra = numero(self.preco_compra)
        preco_venda = numero(self.preco_venda)

        duplicado = next(
            (r for r in await xano.listar(TABELA)
             if ((placa and re.sub(r"[^A-Z0-9]", "", (r.get("placa") or "").upper()) == placa)
                 or (chassi and (r.get("chassi") or "").upper() == chassi))
             and r["id"] != self.form_id),
            None,
        )
        if duplicado:
            self.erro_form = f"Já existe uma moto cadastrada com essa placa ou chassi ({duplicado.get('modelo')})."
            return

        cliente_id = 0 if self.cliente_selecionado == SEM_CLIENTE else int(self.cliente_selecionado.split(" - ")[0])
        data_saida = self.data_saida
        if self.status == "Vendida" and not data_saida:
            data_saida = datetime.date.today().strftime("%Y-%m-%d")

        # Registro COMPLETO — o PATCH do Xano zera o que não for enviado.
        dados = {
            "marca": self.marca.strip(),
            "modelo": modelo,
            "ano": ano,
            "cor": self.cor.strip(),
            "placa": placa,
            "chassi": chassi,
            "quilometragem": quilometragem,
            "status": self.status,
            "em_estoque": self.status not in STATUS_FORA_DO_ESTOQUE,
            "preco_compra": preco_compra,
            "preco_venda": preco_venda,
            "data_entrada": _input_para_epoch(self.data_entrada),
            "data_saida": _input_para_epoch(data_saida),
            "observacoes": self.observacoes.strip(),
            "cliente_id": cliente_id,
            "foto": self._foto or None,
            "fotos": self._fotos_extras or None,
            "renavam": re.sub(r"\D", "", self.renavam),
            "cilindrada": inteiro(self.cilindrada) or None,
            "localizacao": " ".join(self.localizacao.split()),
        }
        if self.form_id is None:
            await xano.criar(TABELA, dados)
            mensagem = f"Moto “{modelo}” cadastrada."
        else:
            await xano.atualizar(TABELA, self.form_id, dados)
            mensagem = f"Moto “{modelo}” atualizada."

        # venda nova (não a mesma venda salva de novo): e-mail de parabéns ao comprador
        venda_nova = self.status == "Vendida" and (self._status_lido != "Vendida" or self._cliente_lido != cliente_id)
        if venda_nova and cliente_id:
            comprador = await xano.buscar(TABELA_CLIENTES, cliente_id)
            moto = " ".join(p for p in (dados["marca"], modelo, str(ano or ""), dados["cor"]) if p)
            if comprador and comprador.get("email") and email_clientes.parabens_compra(
                    comprador.get("nome_cliente") or "", comprador["email"], moto):
                mensagem += " E-mail de parabéns enviado ao cliente."

        self.novo()
        await self.carregar()
        return rx.toast.success(mensagem)

    @rx.event
    async def excluir(self, moto_id: str):
        usos = await em_uso(TABELA, int(moto_id))
        if usos:
            return rx.toast.error(mensagem_em_uso("esta moto", usos))
        await xano.excluir(TABELA, int(moto_id))
        if self.form_id == int(moto_id):
            self.novo()
        await self.carregar()
        return rx.toast.success("Moto excluída.")
