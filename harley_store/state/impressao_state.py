"""
State dos documentos para impressão (rota /imprimir/[doc_tipo]/[doc_id]).

Monta, a partir dos dados do Xano, um documento em formato de folha A4:
    venda   -> comprovante de venda (tabela transacoes)
    os      -> ordem de serviço (ordens_servico + itens_ordem_servico)
    compra  -> entrada de mercadoria (entrada_mercadoria + itens_compra_estoque)
    moto    -> recibo de compra e venda / ficha de moto da loja (motos)

O documento é descrito de forma genérica (até 3 grupos de campos + tabela
de itens + total + assinaturas), e a página pages/impressao.py só desenha.
Para criar um tipo novo, basta escrever mais uma função _montar_<tipo>.
"""

import asyncio
import datetime

import reflex as rx

from .. import pagamentos_servico as pagamentos
from .. import xano_client as xano
from ..vendas_servico import CAMPO_VENDA, esta_cancelada


def _moeda(valor) -> str:
    return "R$ " + f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data_hora(epoch_ms) -> str:
    return xano.epoch_ms_para_datetime(epoch_ms).strftime("%d/%m/%Y %H:%M") if epoch_ms else "—"


def _data(epoch_ms) -> str:
    return xano.epoch_ms_para_datetime(epoch_ms).strftime("%d/%m/%Y") if epoch_ms else "—"


def _texto(valor) -> str:
    return str(valor).strip() if valor not in (None, "", 0) else "—"


def _campos_cliente(cliente: dict | None) -> list[list[str]]:
    if not cliente:
        return [["Cliente", "Não identificado (venda de balcão)"]]
    return [
        ["Nome", _texto(cliente.get("nome_cliente"))],
        ["CPF/CNPJ", _texto(cliente.get("cpf_cnpj"))],
        ["Telefone", _texto(cliente.get("telefone"))],
        ["E-mail", _texto(cliente.get("email"))],
        ["Endereço", _texto(cliente.get("endereco"))],
    ]


def _pagamento(venda: dict) -> str:
    """Forma e situação do pagamento no comprovante (venda antiga: "Não informado")."""
    forma = pagamentos.rotulo_forma(venda.get("forma_pagamento"))
    if not pagamentos.pelo_asaas(venda.get("forma_pagamento") or ""):
        return forma  # "Na loja" ou "Não informado"
    texto = f"{forma} — {pagamentos.rotulo_situacao(venda.get('situacao_pagamento'))}"
    data = pagamentos.data_texto(venda.get("data_pagamento"))
    return f"{texto} em {data}" if data else texto


async def _buscar_ou_none(tabela: str, registro_id) -> dict | None:
    return await xano.buscar(tabela, int(registro_id)) if registro_id else None


class ImpressaoState(rx.State):
    carregando: bool = True
    erro: str = ""

    titulo: str = ""
    numero: str = ""
    emitido_em: str = ""

    grupo1_titulo: str = ""
    grupo1: list[list[str]] = []
    grupo2_titulo: str = ""
    grupo2: list[list[str]] = []
    grupo3_titulo: str = ""
    grupo3: list[list[str]] = []

    itens_titulo: str = ""
    itens_cabecalho: list[str] = []
    itens: list[list[str]] = []
    total_rotulo: str = "TOTAL"
    total: str = ""

    observacoes: str = ""
    termo: str = ""
    assinaturas: list[str] = []
    # faixa de destaque (ex.: "VENDA CANCELADA em ... — motivo: ...")
    faixa: str = ""

    def _limpar(self):
        self.erro = ""
        self.titulo = self.numero = self.total = self.observacoes = self.termo = self.faixa = ""
        self.grupo1_titulo = self.grupo2_titulo = self.grupo3_titulo = self.itens_titulo = ""
        self.grupo1, self.grupo2, self.grupo3 = [], [], []
        self.itens_cabecalho, self.itens, self.assinaturas = [], [], []
        self.total_rotulo = "TOTAL"
        self.emitido_em = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    @rx.event
    async def carregar(self):
        self.carregando = True
        self._limpar()
        yield
        tipo = self.router.page.params.get("doc_tipo", "")
        doc_id = self.router.page.params.get("doc_id", "")
        montar = {
            "venda": self._montar_venda,
            "os": self._montar_os,
            "compra": self._montar_compra,
            "moto": self._montar_moto,
        }.get(tipo)
        try:
            if montar is None or not str(doc_id).isdigit():
                self.erro = "Documento inválido."
            else:
                await montar(int(doc_id))
        except Exception:
            self.erro = "Não foi possível carregar o documento. Tente novamente em instantes."
        self.carregando = False

    async def _montar_venda(self, doc_id: int):
        venda = await xano.buscar("transacoes", doc_id)
        if not venda:
            self.erro = f"Venda nº {doc_id} não encontrada."
            return
        funcionario, cliente, moto = await asyncio.gather(
            _buscar_ou_none("funcionarios", venda.get("id_funcionario")),
            _buscar_ou_none("clientes", venda.get("id_cliente")),
            _buscar_ou_none("motos_clientes", venda.get("id_moto_cliente")),
        )
        try:
            itens_venda = [i for i in await xano.listar("itens_transacao")
                           if int(i.get(CAMPO_VENDA) or 0) == doc_id]
        except Exception:
            itens_venda = []
        tipo = venda.get("tipo_transacao") or "—"
        self.titulo = "COMPROVANTE DE VENDA"
        self.numero = f"Nº {doc_id:06d}"
        self.grupo1_titulo = "Dados da venda"
        self.grupo1 = [
            ["Data", _data_hora(venda.get("data_transacao"))],
            ["Tipo", tipo.replace("_", " ").title()],
            ["Vendedor", _texto((funcionario or {}).get("nome_funcionario"))],
            ["Pagamento", _pagamento(venda)],
        ]
        self.grupo2_titulo = "Cliente"
        self.grupo2 = _campos_cliente(cliente)
        if moto:
            self.grupo3_titulo = "Moto"
            self.grupo3 = [
                ["Modelo", _texto(moto.get("modelo"))],
                ["Placa", _texto(moto.get("placa"))],
                ["Chassi", _texto(moto.get("chassi"))],
            ]
        self.itens_titulo = "Itens"
        if itens_venda:
            self.itens_cabecalho = ["Produto / serviço", "Qtd.", "Unitário", "Subtotal"]
            self.itens = [
                [_texto(i.get("descricao")), str(i.get("quantidade") or 0), _moeda(i.get("valor_unitario")),
                 _moeda((i.get("quantidade") or 0) * float(i.get("valor_unitario") or 0))]
                for i in itens_venda
            ]
        else:
            self.itens_cabecalho = ["Descrição", "Valor"]
            self.itens = [["Itens não registrados (venda anterior ao registro de itens)",
                           _moeda(venda.get("valor_total"))]]
        self.total = _moeda(venda.get("valor_total"))
        self.assinaturas = ["Vendedor", "Cliente"]
        if esta_cancelada(venda):
            quando = venda.get("data_cancelamento")
            quando = (_data_hora(quando) if isinstance(quando, (int, float))
                      else "/".join(reversed(str(quando or "")[:10].split("-"))))
            motivo = venda.get("motivo_cancelamento") or "não informado"
            self.faixa = f"VENDA CANCELADA em {quando or '—'} — motivo: {motivo}"
            self.total_rotulo = "TOTAL (CANCELADO)"

    async def _montar_os(self, doc_id: int):
        ordem = await xano.buscar("ordens_servico", doc_id)
        if not ordem:
            self.erro = f"Ordem de serviço nº {doc_id} não encontrada."
            return
        itens, produtos, mecanico, moto = await asyncio.gather(
            xano.listar("itens_ordem_servico"),
            xano.listar("produtos"),
            _buscar_ou_none("funcionarios", ordem.get("id_funcionario")),
            _buscar_ou_none("motos_clientes", ordem.get("id_moto_cliente")),
        )
        cliente = await _buscar_ou_none("clientes", (moto or {}).get("id_cliente"))
        nomes = {p["id"]: p["nome_produto"] for p in produtos}
        itens_os = [i for i in itens if i.get("id_os") == doc_id]
        total = sum(float(i.get("valor_total_item") or 0) for i in itens_os)

        self.titulo = "ORDEM DE SERVIÇO"
        self.numero = f"Nº {doc_id:06d}"
        self.grupo1_titulo = "Ordem de serviço"
        self.grupo1 = [
            ["Abertura", _data_hora(ordem.get("data_abertura"))],
            ["Status", _texto(ordem.get("status")).replace("_", " ").title()],
            ["Mecânico", _texto((mecanico or {}).get("nome_funcionario"))],
        ]
        self.grupo2_titulo = "Cliente"
        self.grupo2 = _campos_cliente(cliente)
        self.grupo3_titulo = "Moto"
        self.grupo3 = [
            ["Modelo", _texto((moto or {}).get("modelo"))],
            ["Placa", _texto((moto or {}).get("placa"))],
            ["Chassi", _texto((moto or {}).get("chassi"))],
        ]
        self.itens_titulo = "Peças e serviços"
        self.itens_cabecalho = ["Peça / serviço", "Qtd.", "Valor"]
        self.itens = [
            [i.get("descricao") or nomes.get(i.get("id_produto"), "(produto removido)"),
             str(i.get("quantidade") or 0), _moeda(i.get("valor_total_item"))]
            for i in itens_os
        ] or [["Nenhuma peça ou serviço lançado", "", _moeda(0)]]
        self.total = _moeda(total)
        self.termo = ("Autorizo a execução dos serviços descritos acima. Declaro que retirei o veículo "
                      "nas condições descritas e que os serviços foram executados conforme combinado.")
        self.assinaturas = ["Mecânico responsável", "Cliente"]

    async def _montar_compra(self, doc_id: int):
        entrada = await xano.buscar("entrada_mercadoria", doc_id)
        if not entrada:
            self.erro = f"Compra nº {doc_id} não encontrada."
            return
        itens, produtos, fornecedor = await asyncio.gather(
            xano.listar("itens_compra_estoque"),
            xano.listar("produtos"),
            _buscar_ou_none("fornecedores", entrada.get("id_fornecedor")),
        )
        nomes = {p["id"]: p["nome_produto"] for p in produtos}
        itens_compra = [i for i in itens if i.get("id_entrada") == doc_id]

        self.titulo = "ENTRADA DE MERCADORIA"
        self.numero = f"Nº {doc_id:06d}"
        self.grupo1_titulo = "Compra"
        self.grupo1 = [["Data da entrada", _data_hora(entrada.get("data_entrada"))],
                       ["Itens", str(len(itens_compra))]]
        self.grupo2_titulo = "Fornecedor"
        self.grupo2 = [
            ["Razão social", _texto((fornecedor or {}).get("nome_fornecedor"))],
            ["CNPJ", _texto((fornecedor or {}).get("cnpj"))],
            ["Contato", _texto((fornecedor or {}).get("contato"))],
        ]
        self.itens_titulo = "Itens recebidos"
        self.itens_cabecalho = ["Produto", "Qtd.", "Valor unit.", "Subtotal"]
        self.itens = [
            [nomes.get(i.get("id_produto"), "(produto removido)"), str(i.get("quantidade") or 0),
             _moeda(i.get("valor_unitario")),
             _moeda((i.get("quantidade") or 0) * float(i.get("valor_unitario") or 0))]
            for i in itens_compra
        ]
        self.total = _moeda(entrada.get("valor_total"))
        self.termo = "Declaro que conferi as mercadorias acima, recebidas em perfeitas condições."
        self.assinaturas = ["Conferido por (Harley Store)", "Fornecedor / entregador"]

    async def _montar_moto(self, doc_id: int):
        moto = await xano.buscar("motos", doc_id)
        if not moto:
            self.erro = f"Moto nº {doc_id} não encontrada."
            return
        cliente = await _buscar_ou_none("clientes", moto.get("cliente_id"))
        vendida = moto.get("status") == "Vendida"
        descricao = f"{_texto(moto.get('marca'))} {_texto(moto.get('modelo'))}".strip()

        self.titulo = "RECIBO DE COMPRA E VENDA DE VEÍCULO" if vendida else "FICHA DO VEÍCULO"
        self.numero = f"Nº {doc_id:06d}"
        self.grupo1_titulo = "Veículo"
        self.grupo1 = [
            ["Marca / modelo", descricao],
            ["Ano", _texto(moto.get("ano"))],
            ["Cor", _texto(moto.get("cor"))],
            ["Placa", _texto(moto.get("placa"))],
            ["Chassi", _texto(moto.get("chassi"))],
            ["Quilometragem", f"{int(moto.get('quilometragem') or 0):,} km".replace(",", ".")],
        ]
        self.grupo2_titulo = "Comprador" if vendida else "Cliente interessado"
        self.grupo2 = _campos_cliente(cliente) if cliente else [["Cliente", "—"]]
        self.grupo3_titulo = "Negociação"
        self.grupo3 = [
            ["Situação", _texto(moto.get("status"))],
            ["Data da venda" if vendida else "Data de entrada",
             _data(moto.get("data_saida") if vendida else moto.get("data_entrada"))],
        ]
        self.itens_titulo = "Valor"
        self.itens_cabecalho = ["Descrição", "Valor"]
        self.itens = [[descricao, _moeda(moto.get("preco_venda"))]]
        self.total_rotulo = "VALOR DA VENDA" if vendida else "PREÇO DE VENDA"
        self.total = _moeda(moto.get("preco_venda"))
        self.observacoes = moto.get("observacoes") or ""
        if vendida:
            self.termo = ("O vendedor declara ter recebido do comprador o valor acima pela venda do veículo "
                          "descrito, que é entregue livre de ônus, e o comprador declara recebê-lo no estado "
                          "em que se encontra.")
            self.assinaturas = ["Vendedor (Harley Store)", "Comprador"]
        else:
            self.assinaturas = ["Vendedor (Harley Store)", "Cliente"]
