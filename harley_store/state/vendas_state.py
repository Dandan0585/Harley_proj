"""
State de Vendas / Balcão (tabelas transacoes + itens_transacao).

Uma venda tem vários itens (carrinho): produtos do estoque ou itens avulsos
(sem estoque, ex.: mão de obra). Vendas não são apagadas: são CANCELADAS,
continuam na lista, saem do faturamento e devolvem o estoque. As regras
(ordem das gravações, travas de estoque, compensação de falhas) ficam em
`vendas_servico.py`; aqui fica só o que a tela precisa.

Vendas registradas antes dos itens existirem não têm itens gravados: são
exibidas com o valor total e, se canceladas, o sistema avisa para conferir o
estoque manualmente.

Observação: por causa da importação por CSV, "sem cliente/moto" em
`transacoes` é `0`, não `null`.

Moto da loja (tabela `motos`): o Balcão lista as disponíveis, mostra preço e
dados, e a moto entra no carrinho como item com `id_moto` (no máximo uma por
venda, com cliente). O servidor relê preço e dados (vendas_servico).

Pagamento (change pagamento-de-vendas-pelo-asaas): forma de pagamento e
vencimento na conclusão da venda; nas formas pelo Asaas, a cobrança é gerada
no servidor (pagamentos_servico). A lista mostra a situação do pagamento, o
link da cobrança e os botões "Gerar cobrança de novo" e "Atualizar pagamentos".
"""

import asyncio

import reflex as rx

from .. import asaas_client
from .. import pagamentos_servico as pagamentos
from .. import vendas_servico as servico
from .. import xano_client as xano
from ..constantes import TIPOS_VENDA
from .auth_state import AuthState
from .motos_loja_state import _linha_moto

TABELA = "transacoes"
TABELA_ITENS = "itens_transacao"
TABELA_FUNCIONARIOS = "funcionarios"
TABELA_CLIENTES = "clientes"
TABELA_MOTOS = "motos_clientes"
TABELA_PRODUTOS = "produtos"
TABELA_MOTOS_LOJA = "motos"

# dados da moto da loja mostrados no Balcão (vêm de motos_loja_state._linha_moto)
CAMPOS_MOTO_LOJA = ("id", "marca", "modelo", "ano", "cor", "placa", "chassi", "renavam", "cilindrada",
                    "quilometragem", "status", "preco_venda", "foto_url")

SEM_CLIENTE = "— nenhum —"
SEM_MOTO = "— nenhuma —"


def _numero(texto: str) -> float:
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto) if texto else 0.0


def _moeda(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data_cancelamento(valor) -> str:
    """O campo pode ser timestamp (epoch ms) ou date ('AAAA-MM-DD') no Xano."""
    if not valor:
        return ""
    if isinstance(valor, (int, float)):
        return xano.epoch_ms_para_datetime(valor).strftime("%d/%m/%Y %H:%M")
    partes = str(valor)[:10].split("-")
    return "/".join(reversed(partes)) if len(partes) == 3 else str(valor)


class VendasState(rx.State):
    transacoes: list[dict] = []
    aviso_itens: str = ""  # tabela de itens indisponível no Xano

    funcionarios_opcoes: list[str] = []
    clientes_opcoes: list[str] = []
    motos_opcoes: list[str] = []
    produtos_opcoes: list[str] = []
    motos_loja_opcoes: list[str] = []

    # cabeçalho da venda
    tipo_transacao: str = TIPOS_VENDA[0]
    funcionario_selecionado: str = ""
    cliente_selecionado: str = SEM_CLIENTE
    moto_selecionada: str = SEM_MOTO

    # carrinho: [{id_produto, id_moto, descricao, quantidade, valor_unitario, subtotal}] (strings para a tela)
    carrinho: list[dict] = []
    moto_loja_selecionada: str = ""
    moto_loja: dict[str, str] = {}  # dados da moto escolhida ({} = nenhuma)
    produto_selecionado: str = ""
    item_quantidade: str = "1"
    item_preco: str = ""
    avulso_descricao: str = ""
    avulso_quantidade: str = "1"
    avulso_valor: str = ""

    # pagamento (textos da tela; o código vem de pagamentos.FORMAS)
    asaas_ligado: bool = False
    formas_opcoes: list[str] = [pagamentos.FORMAS[pagamentos.NA_LOJA]]
    forma_pagamento: str = pagamentos.FORMAS[pagamentos.NA_LOJA]
    vencimento: str = ""

    erro_venda: str = ""
    sucesso_venda: str = ""

    # cancelamento
    selecionadas: list[str] = []
    motivo_cancelamento: str = ""
    resultado_cancelamento: list[str] = []

    _precos: dict[int, float] = {}
    _estoques: dict[int, int] = {}
    _nomes: dict[int, str] = {}
    _motos_loja: dict[int, dict] = {}  # registros das motos disponíveis, por id

    @rx.var
    def total_carrinho(self) -> str:
        total = sum(int(i["quantidade"]) * _numero(i["valor_unitario"]) for i in self.carrinho)
        return _moeda(total)

    @rx.var
    def tem_moto_no_carrinho(self) -> bool:
        return any(i["id_moto"] != "0" for i in self.carrinho)

    @rx.var
    def qtd_selecionadas(self) -> int:
        return len(self.selecionadas)

    @rx.var
    def cobra_pelo_asaas(self) -> bool:
        return self.forma_pagamento != pagamentos.FORMAS[pagamentos.NA_LOJA]

    def _codigo_forma(self) -> str:
        return next((c for c, texto in pagamentos.FORMAS.items() if texto == self.forma_pagamento),
                    self.forma_pagamento)

    # ------------------------------------------------------------ carregar

    @rx.event
    async def carregar(self):
        funcionarios, clientes, motos, produtos, transacoes, motos_loja = await asyncio.gather(
            xano.listar(TABELA_FUNCIONARIOS), xano.listar(TABELA_CLIENTES), xano.listar(TABELA_MOTOS),
            xano.listar(TABELA_PRODUTOS), xano.listar(TABELA), xano.listar(TABELA_MOTOS_LOJA),
        )
        try:
            itens = await xano.listar(TABELA_ITENS)
            self.aviso_itens = ""
        except Exception:
            itens = []
            self.aviso_itens = ("A tabela itens_transacao não está disponível no Xano: "
                                "não é possível registrar nem cancelar vendas com devolução de estoque.")
        funcionarios.sort(key=lambda f: f["nome_funcionario"])
        clientes.sort(key=lambda c: c["nome_cliente"])
        motos.sort(key=lambda m: m["modelo"])
        produtos.sort(key=lambda p: p["nome_produto"])
        self._precos = {p["id"]: float(p["preco_venda"] or 0) for p in produtos}
        self._estoques = {p["id"]: int(p["estoque_qtd"] or 0) for p in produtos}
        self._nomes = {p["id"]: p["nome_produto"] for p in produtos}

        self.funcionarios_opcoes = [f"{f['id']} - {f['nome_funcionario']}" for f in funcionarios]
        self.clientes_opcoes = [SEM_CLIENTE] + [f"{c['id']} - {c['nome_cliente']}" for c in clientes]
        self.motos_opcoes = [SEM_MOTO] + [f"{m['id']} - {m['modelo']} ({m['placa']})" for m in motos]
        self.produtos_opcoes = [
            f"{p['id']} - {p['nome_produto']} — estoque {p['estoque_qtd']}" for p in produtos
        ]
        if not self.funcionario_selecionado and self.funcionarios_opcoes:
            self.funcionario_selecionado = self.funcionarios_opcoes[0]

        self.asaas_ligado = asaas_client.configurado()
        self.formas_opcoes = (list(pagamentos.FORMAS.values()) if self.asaas_ligado
                              else [pagamentos.FORMAS[pagamentos.NA_LOJA]])
        if self.forma_pagamento not in self.formas_opcoes:
            self.forma_pagamento = pagamentos.FORMAS[pagamentos.NA_LOJA]
        if not self.vencimento:
            self.vencimento = pagamentos.vencimento_padrao()

        disponiveis = sorted(
            (m for m in motos_loja if (m.get("status") or servico.MOTO_EM_ESTOQUE) not in servico.MOTOS_FORA_DA_VENDA),
            key=lambda m: ((m.get("marca") or "").lower(), (m.get("modelo") or "").lower(), m.get("ano") or 0),
        )
        self._motos_loja = {m["id"]: m for m in disponiveis}
        self.motos_loja_opcoes = [
            f"{m['id']} - {servico.nome_moto(m)} — R$ {_moeda(float(m.get('preco_venda') or 0))}" for m in disponiveis
        ]
        if self.moto_loja_selecionada not in self.motos_loja_opcoes:
            self.moto_loja_selecionada, self.moto_loja = "", {}

        nomes_funcionario = {f["id"]: f["nome_funcionario"] for f in funcionarios}
        nomes_cliente = {c["id"]: c["nome_cliente"] for c in clientes}
        itens_por_venda: dict[int, int] = {}
        for item in itens:
            vid = int(item.get(servico.CAMPO_VENDA) or 0)
            itens_por_venda[vid] = itens_por_venda.get(vid, 0) + 1

        registros = sorted(transacoes, key=lambda t: t["data_transacao"] or 0, reverse=True)[:50]
        self.transacoes = [
            {
                "id": str(t["id"]),
                "tipo_transacao": t["tipo_transacao"],
                "funcionario_nome": nomes_funcionario.get(t["id_funcionario"], "—"),
                "cliente_nome": nomes_cliente.get(t["id_cliente"], "—") if t.get("id_cliente") else "—",
                "data_transacao": xano.epoch_ms_para_datetime(t["data_transacao"]).strftime("%d/%m/%Y %H:%M"),
                "valor_total": _moeda(float(t["valor_total"] or 0)),
                "cancelada": servico.esta_cancelada(t),
                "data_cancelamento": _data_cancelamento(t.get("data_cancelamento")),
                "motivo": t.get("motivo_cancelamento") or "",
                "qtd_itens": str(itens_por_venda[t["id"]]) if t["id"] in itens_por_venda else "—",
                "forma": pagamentos.rotulo_forma(t.get("forma_pagamento")),
                "pagamento": pagamentos.rotulo_situacao(t.get("situacao_pagamento")),
                "situacao_pagamento": t.get("situacao_pagamento") or "",
                "data_pagamento": pagamentos.data_texto(t.get("data_pagamento")),
                "link_cobranca": t.get("link_cobranca") or "",
                "pode_cobrar": (not servico.esta_cancelada(t)
                                and t.get("situacao_pagamento") == pagamentos.SEM_COBRANCA),
            }
            for t in registros
        ]
        ativas = {t["id"] for t in self.transacoes if not t["cancelada"]}
        self.selecionadas = [i for i in self.selecionadas if i in ativas]

    # ------------------------------------------------------------ carrinho

    @rx.event
    def definir_produto(self, valor: str):
        self.produto_selecionado = valor
        try:
            pid = int(valor.split(" - ")[0])
            self.item_preco = _moeda(self._precos.get(pid, 0.0))
        except ValueError:
            pass

    @rx.event
    def adicionar_produto(self):
        self.erro_venda = self.sucesso_venda = ""
        if not self.produto_selecionado:
            self.erro_venda = "Escolha um produto."
            return
        try:
            pid = int(self.produto_selecionado.split(" - ")[0])
            qtd = int(self.item_quantidade or 0)
            preco = _numero(self.item_preco)
        except ValueError:
            self.erro_venda = "Quantidade e preço precisam ser números."
            return
        if qtd <= 0 or preco < 0:
            self.erro_venda = "A quantidade precisa ser maior que zero e o preço não pode ser negativo."
            return
        ja_no_carrinho = sum(int(i["quantidade"]) for i in self.carrinho if int(i["id_produto"]) == pid)
        disponivel = self._estoques.get(pid, 0)
        if ja_no_carrinho + qtd > disponivel:
            self.erro_venda = f"Estoque insuficiente de {self._nomes.get(pid, 'produto')}: há {disponivel}."
            return
        self.carrinho = self.carrinho + [{
            "id_produto": str(pid),
            "id_moto": "0",
            "descricao": self._nomes.get(pid, f"Produto {pid}"),
            "quantidade": str(qtd),
            "valor_unitario": _moeda(preco),
            "subtotal": _moeda(qtd * preco),
        }]
        self.item_quantidade = "1"

    @rx.event
    def adicionar_avulso(self):
        self.erro_venda = self.sucesso_venda = ""
        descricao = self.avulso_descricao.strip()
        try:
            qtd = int(self.avulso_quantidade or 0)
            valor = _numero(self.avulso_valor)
        except ValueError:
            self.erro_venda = "Quantidade e valor precisam ser números."
            return
        if not descricao or qtd <= 0 or valor < 0:
            self.erro_venda = "Informe a descrição, uma quantidade maior que zero e um valor válido."
            return
        self.carrinho = self.carrinho + [{
            "id_produto": "0",
            "id_moto": "0",
            "descricao": descricao,
            "quantidade": str(qtd),
            "valor_unitario": _moeda(valor),
            "subtotal": _moeda(qtd * valor),
        }]
        self.avulso_descricao, self.avulso_quantidade, self.avulso_valor = "", "1", ""

    @rx.event
    def definir_moto_loja(self, valor: str):
        self.moto_loja_selecionada = valor
        try:
            moto = self._motos_loja.get(int(valor.split(" - ")[0]))
        except ValueError:
            moto = None
        linha = _linha_moto(moto, {}) if moto else {}
        self.moto_loja = {campo: linha[campo] for campo in CAMPOS_MOTO_LOJA} if linha else {}

    @rx.event
    def adicionar_moto(self):
        """A moto entra pelo preço do cadastro; o servidor confere tudo de novo ao registrar."""
        self.erro_venda = self.sucesso_venda = ""
        if not self.moto_loja:
            self.erro_venda = "Escolha uma moto da loja."
            return
        if self.tem_moto_no_carrinho:
            self.erro_venda = "Só é possível vender uma moto da loja por venda."
            return
        moto = self._motos_loja.get(int(self.moto_loja["id"]))
        problema = servico.problema_moto(moto)
        if problema:
            self.erro_venda = problema
            return
        preco = float(moto["preco_venda"])
        self.carrinho = self.carrinho + [{
            "id_produto": "0",
            "id_moto": str(moto["id"]),
            "descricao": servico.descricao_moto(moto),
            "quantidade": "1",
            "valor_unitario": _moeda(preco),
            "subtotal": _moeda(preco),
        }]
        self.tipo_transacao = "MOTO"
        self.moto_selecionada = SEM_MOTO  # a moto comprada vira a moto do cliente ao registrar
        self.moto_loja_selecionada, self.moto_loja = "", {}

    @rx.event
    def remover_item(self, indice: int):
        self.carrinho = [item for i, item in enumerate(self.carrinho) if i != indice]

    @rx.event
    def nova_venda(self):
        self.tipo_transacao = TIPOS_VENDA[0]
        self.cliente_selecionado = SEM_CLIENTE
        self.moto_selecionada = SEM_MOTO
        self.carrinho = []
        self.produto_selecionado = ""
        self.item_quantidade, self.item_preco = "1", ""
        self.avulso_descricao, self.avulso_quantidade, self.avulso_valor = "", "1", ""
        self.moto_loja_selecionada, self.moto_loja = "", {}
        self.forma_pagamento = pagamentos.FORMAS[pagamentos.NA_LOJA]
        self.vencimento = pagamentos.vencimento_padrao()
        self.erro_venda = ""

    @rx.event
    async def salvar(self):
        self.erro_venda = self.sucesso_venda = ""
        if not self.funcionario_selecionado:
            self.erro_venda = "Cadastre um funcionário antes de registrar uma venda."
            return
        if not self.carrinho:
            self.erro_venda = "Adicione ao menos um item à venda."
            return
        if self.tem_moto_no_carrinho and self.cliente_selecionado == SEM_CLIENTE:
            self.erro_venda = "Para vender uma moto da loja, escolha o cliente comprador."
            return
        if self.cobra_pelo_asaas and self.cliente_selecionado == SEM_CLIENTE:
            self.erro_venda = "Para cobrar pelo Asaas, escolha o cliente da venda."
            return
        itens = [
            {"id_produto": int(i["id_produto"]), "id_moto": int(i["id_moto"]), "descricao": i["descricao"],
             "quantidade": int(i["quantidade"]), "valor_unitario": _numero(i["valor_unitario"])}
            for i in self.carrinho
        ]
        id_cliente = 0 if self.cliente_selecionado == SEM_CLIENTE else int(self.cliente_selecionado.split(" - ")[0])
        id_moto = 0 if self.moto_selecionada == SEM_MOTO else int(self.moto_selecionada.split(" - ")[0])
        try:
            venda_id, avisos = await servico.registrar_venda(
                self.tipo_transacao, int(self.funcionario_selecionado.split(" - ")[0]),
                id_cliente, id_moto, itens, (await self.get_state(AuthState)).usuario_logado,
                self._codigo_forma(), self.vencimento if self.cobra_pelo_asaas else "",
            )
        except servico.FalhaVenda as erro:
            self.erro_venda = str(erro)
            await self.carregar()
            return
        total = self.total_carrinho
        self.nova_venda()
        self.sucesso_venda = " ".join([f"Venda nº {venda_id} registrada: R$ {total}.", *avisos])
        await self.carregar()

    # -------------------------------------------------------- cancelamento

    @rx.event
    def preparar_cancelamento(self):
        self.motivo_cancelamento = ""

    @rx.event
    def alternar_selecao(self, venda_id: str):
        if venda_id in self.selecionadas:
            self.selecionadas = [i for i in self.selecionadas if i != venda_id]
        else:
            self.selecionadas = self.selecionadas + [venda_id]

    @rx.event
    def limpar_selecao(self):
        self.selecionadas = []

    def _resumir(self, resultados: list[dict]):
        canceladas = [r for r in resultados if r["situacao"] == "cancelada"]
        linhas = []
        if canceladas:
            linhas.append(f"{len(canceladas)} vendas canceladas." if len(canceladas) > 1
                          else f"Venda nº {canceladas[0]['id']} cancelada.")
        linhas += [r["mensagem"] for r in resultados if r["mensagem"]]
        self.resultado_cancelamento = linhas

    @rx.event
    async def cancelar(self, venda_id: str):
        usuario = (await self.get_state(AuthState)).usuario_logado
        resultado = await servico.cancelar_venda(int(venda_id), self.motivo_cancelamento, usuario)
        resultado["id"] = int(venda_id)
        self._resumir([resultado])
        self.selecionadas = [i for i in self.selecionadas if i != venda_id]
        await self.carregar()

    @rx.event
    async def cancelar_selecionadas(self):
        ids = [int(i) for i in self.selecionadas]
        if not ids:
            return
        usuario = (await self.get_state(AuthState)).usuario_logado
        resultados = await servico.cancelar_varias(ids, self.motivo_cancelamento, usuario)
        self._resumir(resultados)
        self.selecionadas = []
        await self.carregar()

    @rx.event
    def fechar_resultado(self):
        self.resultado_cancelamento = []

    # ------------------------------------------------------------ pagamento

    @rx.event
    async def gerar_cobranca(self, venda_id: str):
        """Nova tentativa para venda em "Falha na cobrança" (não duplica a cobrança)."""
        _, mensagem = await pagamentos.gerar_cobranca(int(venda_id))
        self.resultado_cancelamento = [mensagem]
        await self.carregar()

    @rx.event
    async def atualizar_pagamentos(self):
        if not asaas_client.configurado():
            self.resultado_cancelamento = ["A integração com o Asaas não está configurada no servidor."]
            return
        resumo = await pagamentos.atualizar_pagamentos()
        linhas = [f"{resumo['consultadas']} cobrança(s) em aberto consultada(s) no Asaas; "
                  f"{resumo['alteradas']} com situação nova, {resumo['pagas']} paga(s)."]
        if resumo["pagas"]:
            linhas.append("O e-mail de confirmação foi enviado aos clientes com e-mail.")
        if resumo["erros"]:
            linhas.append(f"{resumo['erros']} não puderam ser consultada(s) agora: tente de novo em instantes.")
        self.resultado_cancelamento = linhas
        await self.carregar()
