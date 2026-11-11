"""State de Ordens de Serviço (OrdemServico + ItemOrdemServico). Dados vêm do backend Xano.

Estoque: as peças lançadas numa OS saem do estoque ao abrir a OS, pela
mesma rotina protegida das vendas (`estoque.movimentar`): se faltar
estoque de alguma peça, nada é gravado. Excluir uma OS devolve as peças ao
estoque. Se uma gravação falhar no meio, o que já foi feito é desfeito.

Faturamento: ao marcar a OS como CONCLUIDA, grava-se `data_conclusao`, e o
valor da OS (peças + mão de obra) entra no faturamento desse dia no Painel.
Se ela sair de CONCLUIDA, a data é apagada e o valor sai do faturamento.
"""

import asyncio
import logging

import reflex as rx

from .. import estoque
from .. import xano_client as xano
from ..constantes import STATUS_OS
from ..validacao import inteiro, numero
from .auth_state import AuthState

log = logging.getLogger("harley_store.os")

TABELA_OS = "ordens_servico"
TABELA_ITENS = "itens_ordem_servico"
TABELA_MOTOS = "motos_clientes"
TABELA_FUNCIONARIOS = "funcionarios"
TABELA_PRODUTOS = "produtos"
TABELA_CLIENTES = "clientes"


class OrdensServicoState(rx.State):
    ordens: list[dict] = []

    motos_opcoes: list[str] = []
    mecanicos_opcoes: list[str] = []
    produtos_opcoes: list[str] = []

    moto_selecionada: str = ""
    mecanico_selecionado: str = ""
    itens_atual: list[dict] = []  # [{produto_id, produto_nome, quantidade, valor_total_item}]

    item_produto_selecionado: str = ""
    item_quantidade: str = "1"
    item_valor_total: str = "0.00"

    # serviço / mão de obra (sem estoque)
    servico_descricao: str = ""
    servico_valor: str = ""

    erro_os: str = ""

    _precos: dict[int, float] = {}
    _estoques: dict[int, int] = {}

    @rx.var
    def total_atual(self) -> str:
        total = sum(float(item["valor_total_item"]) for item in self.itens_atual)
        return f"{total:.2f}"

    @rx.event
    async def carregar(self):
        # As tabelas são buscadas em paralelo (em sequência eram várias esperas).
        motos, todos_funcionarios, produtos, ordens, itens, clientes = await asyncio.gather(
            xano.listar(TABELA_MOTOS), xano.listar(TABELA_FUNCIONARIOS), xano.listar(TABELA_PRODUTOS),
            xano.listar(TABELA_OS), xano.listar(TABELA_ITENS), xano.listar(TABELA_CLIENTES),
        )
        nomes_cliente = {c["id"]: c.get("nome_cliente") or "" for c in clientes}
        motos.sort(key=lambda m: (m.get("modelo") or "").lower())
        mecanicos = sorted(
            [f for f in todos_funcionarios if f.get("tipo") == "MECANICO"],
            key=lambda f: (f.get("nome_funcionario") or "").lower(),
        )
        produtos.sort(key=lambda p: (p.get("nome_produto") or "").lower())
        self._precos = {p["id"]: float(p.get("preco_venda") or 0) for p in produtos}
        self._estoques = {p["id"]: int(p.get("estoque_qtd") or 0) for p in produtos}

        self.motos_opcoes = [
            f"{m['id']} - {m.get('modelo')} ({m.get('placa')}) — {nomes_cliente.get(m.get('id_cliente'), 'sem cliente')}"
            for m in motos
        ]
        self.mecanicos_opcoes = [f"{f['id']} - {f['nome_funcionario']}" for f in mecanicos]
        self.produtos_opcoes = [
            f"{p['id']} - {p.get('nome_produto')} — estoque {p.get('estoque_qtd') or 0}" for p in produtos
        ]
        # seleções que deixaram de existir (registro excluído) são descartadas
        if self.moto_selecionada not in self.motos_opcoes:
            self.moto_selecionada = self.motos_opcoes[0] if self.motos_opcoes else ""
        if self.mecanico_selecionado not in self.mecanicos_opcoes:
            self.mecanico_selecionado = self.mecanicos_opcoes[0] if self.mecanicos_opcoes else ""
        if self.item_produto_selecionado not in self.produtos_opcoes:
            self.item_produto_selecionado = ""
            self.item_valor_total = "0.00"

        nomes_moto = {m["id"]: f"{m.get('modelo')} ({m.get('placa')})" for m in motos}
        # também pode haver mecânicos já cadastrados com outro tipo em OS antigas
        nomes_mecanico = {f["id"]: f["nome_funcionario"] for f in todos_funcionarios}

        registros = sorted(ordens, key=lambda o: o.get("data_abertura") or 0, reverse=True)[:30]
        qtd_itens_por_os: dict[int, int] = {}
        valor_por_os: dict[int, float] = {}
        for item in itens:
            os_id = item.get("id_os")
            qtd_itens_por_os[os_id] = qtd_itens_por_os.get(os_id, 0) + 1
            valor_por_os[os_id] = valor_por_os.get(os_id, 0.0) + float(item.get("valor_total_item") or 0)

        self.ordens = [
            {
                "id": str(o["id"]),
                "data_abertura": xano.epoch_ms_para_datetime(o.get("data_abertura")).strftime("%d/%m/%Y %H:%M"),
                "moto_nome": nomes_moto.get(o.get("id_moto_cliente"), "(moto removida)"),
                "mecanico_nome": nomes_mecanico.get(o.get("id_funcionario"), "—"),
                "status": o.get("status") or "ABERTA",
                "qtd_itens": str(qtd_itens_por_os.get(o["id"], 0)),
                "valor_total": f"{valor_por_os.get(o['id'], 0.0):.2f}",
            }
            for o in registros
        ]

    def _id_produto_selecionado(self) -> int:
        try:
            return int(self.item_produto_selecionado.split(" - ")[0])
        except ValueError:
            return 0

    def _sugerir_valor(self):
        pid = self._id_produto_selecionado()
        try:
            qtd = max(inteiro(self.item_quantidade), 0)
        except ValueError:
            return
        if pid:
            self.item_valor_total = f"{self._precos.get(pid, 0.0) * qtd:.2f}"

    @rx.event
    def definir_item_produto(self, valor: str):
        """Escolher a peça já sugere o valor (preço de venda × quantidade)."""
        self.item_produto_selecionado = valor
        self._sugerir_valor()

    @rx.event
    def definir_item_quantidade(self, valor: str):
        self.item_quantidade = valor
        self._sugerir_valor()

    @rx.event
    def adicionar_item(self):
        self.erro_os = ""
        pid = self._id_produto_selecionado()
        if not pid:
            self.erro_os = "Escolha a peça (produto) que será usada."
            return
        try:
            quantidade = inteiro(self.item_quantidade)
            valor_total_item = numero(self.item_valor_total)
        except ValueError:
            self.erro_os = "Quantidade e valor precisam ser números válidos."
            return
        if quantidade <= 0:
            self.erro_os = "A quantidade precisa ser maior que zero."
            return
        if valor_total_item < 0:
            self.erro_os = "O valor não pode ser negativo."
            return
        ja_lancado = sum(int(i["quantidade"]) for i in self.itens_atual if int(i["produto_id"]) == pid)
        disponivel = self._estoques.get(pid, 0)
        if ja_lancado + quantidade > disponivel:
            self.erro_os = f"Estoque insuficiente dessa peça: há {disponivel}."
            return

        produto_nome = self.item_produto_selecionado.split(" - ", 1)[1].rsplit(" — estoque", 1)[0]
        self.itens_atual = self.itens_atual + [
            {
                "produto_id": str(pid),
                "produto_nome": produto_nome,
                "quantidade": str(quantidade),
                "valor_total_item": f"{valor_total_item:.2f}",
            }
        ]
        self.item_quantidade = "1"
        self._sugerir_valor()

    @rx.event
    def adicionar_servico(self):
        """Serviço / mão de obra: vai na OS com descrição e valor, sem mexer no estoque."""
        self.erro_os = ""
        descricao = " ".join(self.servico_descricao.split())
        try:
            valor = numero(self.servico_valor)
        except ValueError:
            self.erro_os = "O valor do serviço precisa ser um número válido (ex.: 250,00)."
            return
        if not descricao:
            self.erro_os = "Descreva o serviço (ex.: troca de óleo, revisão de 10.000 km)."
            return
        if valor < 0:
            self.erro_os = "O valor do serviço não pode ser negativo."
            return
        self.itens_atual = self.itens_atual + [
            {"produto_id": "0", "produto_nome": descricao, "quantidade": "1", "valor_total_item": f"{valor:.2f}"}
        ]
        self.servico_descricao, self.servico_valor = "", ""

    @rx.event
    def remover_item(self, indice: int):
        self.itens_atual = [item for i, item in enumerate(self.itens_atual) if i != indice]

    @rx.event
    async def abrir_os(self):
        self.erro_os = ""
        if not self.moto_selecionada:
            self.erro_os = "Cadastre uma moto de cliente antes de abrir uma OS."
            return
        if not self.mecanico_selecionado:
            self.erro_os = "Cadastre um funcionário do tipo MECANICO antes de abrir uma OS."
            return

        id_moto = int(self.moto_selecionada.split(" - ")[0])
        id_mecanico = int(self.mecanico_selecionado.split(" - ")[0])
        baixas: dict[int, int] = {}
        for item in self.itens_atual:
            pid = int(item["produto_id"])
            if pid:  # serviço (id 0) não mexe no estoque
                baixas[pid] = baixas.get(pid, 0) - int(item["quantidade"])

        # 1) baixa todas as peças, ou nenhuma
        try:
            saldos = await estoque.movimentar(baixas)
        except estoque.EstoqueInsuficiente as erro:
            self.erro_os = "Estoque insuficiente: " + ", ".join(erro.produtos) + ". Nada foi gravado."
            await self.carregar()
            return
        except estoque.ProdutoInexistente as erro:
            self.erro_os = f"{erro} Remova a peça e tente de novo."
            return
        devolucao = {pid: -qtd for pid, qtd in baixas.items()}

        # 2) cabeçalho e itens; se algo falhar, desfaz tudo
        os_nova = None
        criados: list[int] = []
        try:
            os_nova = await xano.criar(TABELA_OS, {
                "id_moto_cliente": id_moto,
                "id_funcionario": id_mecanico,
                "data_abertura": xano.datetime_para_epoch_ms(),
                "status": "ABERTA",
            })
            for item in self.itens_atual:
                gravado = await xano.criar(TABELA_ITENS, {
                    "id_os": os_nova["id"],
                    "id_produto": int(item["produto_id"]),
                    "quantidade": int(item["quantidade"]),
                    "valor_total_item": float(item["valor_total_item"]),
                    "descricao": item["produto_nome"],
                })
                criados.append(int(gravado["id"]))
        except Exception:
            log.exception("falha ao gravar a OS; desfazendo")
            for item_id in criados:
                try:
                    await xano.excluir(TABELA_ITENS, item_id)
                except Exception:
                    log.exception("nao foi possivel apagar o item %s da OS incompleta", item_id)
            if os_nova:
                try:
                    await xano.excluir(TABELA_OS, int(os_nova["id"]))
                except Exception:
                    log.exception("nao foi possivel apagar a OS incompleta %s", os_nova.get("id"))
            try:
                await estoque.movimentar(devolucao)
            except Exception:
                log.exception("nao foi possivel devolver o estoque da OS incompleta: %s", devolucao)
                self.erro_os = ("A OS não pôde ser gravada e o estoque das peças NÃO pôde ser devolvido. "
                                "Confira o estoque das peças lançadas.")
                return
            self.erro_os = "A OS não pôde ser gravada (falha de conexão). Nada foi alterado; tente de novo."
            return

        usuario = (await self.get_state(AuthState)).usuario_logado
        await estoque.registrar_historico(baixas, saldos, "OS", int(os_nova["id"]), usuario)
        self.itens_atual = []
        await self.carregar()
        return rx.toast.success(f"OS nº {os_nova['id']} aberta.")

    @rx.event
    async def mudar_status(self, os_id: str, novo_status: str):
        if novo_status not in STATUS_OS:
            return rx.toast.error("Situação inválida.")
        registro = await xano.buscar_direto(TABELA_OS, int(os_id))
        if registro is None:
            await self.carregar()
            return rx.toast.error(f"A OS nº {os_id} não existe mais.")
        anterior = registro.get("status") or "ABERTA"
        registro["status"] = novo_status
        if novo_status == "CONCLUIDA" and anterior != "CONCLUIDA":
            registro["data_conclusao"] = xano.datetime_para_epoch_ms()
        elif novo_status != "CONCLUIDA":
            registro["data_conclusao"] = None
        gravado = await xano.atualizar(TABELA_OS, int(os_id), {k: v for k, v in registro.items() if k != "id"})
        await self.carregar()
        if novo_status == "CONCLUIDA" and anterior != "CONCLUIDA":
            if "data_conclusao" not in gravado:
                log.error("ordens_servico sem o campo data_conclusao no Xano")
                return rx.toast.warning(
                    f"OS nº {os_id} concluída, mas o banco ainda não tem a data de conclusão: ela não entra "
                    "no faturamento. Rode scripts/aplicar_xano.ps1."
                )
            valor = next((o["valor_total"] for o in self.ordens if o["id"] == str(os_id)), "0.00")
            return rx.toast.success(f"OS nº {os_id} concluída: R$ {valor} (peças + mão de obra) no faturamento de hoje.")

    @rx.event
    async def excluir_os(self, os_id: str):
        """Exclui a OS e seus itens, devolvendo as peças ao estoque."""
        os_id_int = int(os_id)
        itens = [i for i in await xano.listar(TABELA_ITENS) if i.get("id_os") == os_id_int]
        devolucao: dict[int, int] = {}
        for item in itens:
            pid = int(item.get("id_produto") or 0)
            if pid:
                devolucao[pid] = devolucao.get(pid, 0) + int(item.get("quantidade") or 0)
        try:
            saldos = await estoque.movimentar(devolucao)
        except estoque.ProdutoInexistente:
            # peça que já não existe: devolve só as que ainda existem
            existentes = {p["id"] for p in await xano.listar(TABELA_PRODUTOS)}
            devolucao = {pid: q for pid, q in devolucao.items() if pid in existentes}
            saldos = await estoque.movimentar(devolucao)
        try:
            for item in itens:
                await xano.excluir(TABELA_ITENS, item["id"])
            await xano.excluir(TABELA_OS, os_id_int)
        except Exception:
            log.exception("falha ao excluir a OS %s; refazendo a baixa das pecas", os_id_int)
            try:
                await estoque.movimentar({pid: -q for pid, q in devolucao.items()})
            except Exception:
                log.exception("nao foi possivel refazer a baixa das pecas da OS %s", os_id_int)
            await self.carregar()
            return rx.toast.error("A OS não pôde ser excluída por completo (falha de conexão). Tente de novo.")
        usuario = (await self.get_state(AuthState)).usuario_logado
        await estoque.registrar_historico(devolucao, saldos, "EXCLUSAO_OS", os_id_int, usuario)
        await self.carregar()
        return rx.toast.success(
            f"OS nº {os_id} excluída." + (" As peças voltaram ao estoque." if devolucao else "")
        )
