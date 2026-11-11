"""
Cliente HTTP para o backend Xano (workspace HARLEY, instância Free).

Os states em `state/` usavam `rx.session()` (SQLModel/SQLite local). Este
módulo troca a fonte de dados pelas APIs REST publicadas no Xano, mantendo
a mesma forma de uso: funções simples que recebem/retornam `dict`.

Detalhes importantes do Xano que este cliente já resolve para quem chama:

- O endpoint PATCH gerado pelo assistente "CRUD Database Operations" do
  Xano exige TODOS os campos obrigatórios da tabela (não é um PATCH
  parcial de verdade) — por isso `update()` espera o registro completo,
  não só os campos alterados.
- Campos de data/hora voltam do Xano como epoch em milissegundos (int),
  não como string ISO. `epoch_ms_para_datetime` / `datetime_para_epoch_ms`
  fazem a conversão nos dois sentidos.
- O plano Free do Xano tem limite de requisições por minuto. Como
  algumas telas (ex.: Painel, Compras, Vendas, Ordens de Serviço) fazem
  várias chamadas em sequência para montar os menus/relatórios, é fácil
  esbarrar nesse limite (erro 429) mesmo em uso normal. `_request` faz
  retentativas automáticas com espera crescente antes de desistir.

Todas as funções aqui são `async` e usam `httpx.AsyncClient` (não
`httpx.request` síncrono). Isso importa especialmente no Reflex: um
event handler síncrono que faz uma chamada de rede bloqueante trava a
única thread do loop de eventos do app inteiro enquanto espera — nesse
tempo o servidor não consegue nem responder ao ping/pong do websocket,
e o navegador chega a mostrar "Cannot connect to server" mesmo com o
back-end vivo, só ocupado. Usando `await` em vez de chamada bloqueante,
o loop de eventos fica livre para atender outras coisas (incluindo o
próprio heartbeat da conexão) enquanto a resposta do Xano não chega.
"""

from __future__ import annotations

import asyncio
import copy
import datetime
import logging
import os
import time
from pathlib import Path

import httpx

log = logging.getLogger("harley_store.xano")

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:LtU_pM2N"
AUTH_URL = "https://x8ki-letl-twmt.n7.xano.io/api:lH_WsSPl"
_TIMEOUT = 30.0  # o Xano Free às vezes leva >15 s; esperar é melhor que falhar uma venda


# ------------------------------------------------------------ conta de serviço
# A API de dados do Xano exige login. O SERVIDOR do app acessa os dados com
# uma conta de serviço própria (não a do funcionário), porque o cache e a
# tarefa de fundo não pertencem a nenhum usuário; quem está logado é
# conferido à parte (state/auth_state.py). As credenciais ficam no arquivo
# .env da pasta do projeto (fora do git), com as linhas:
#     HARLEY_XANO_EMAIL=...
#     HARLEY_XANO_SENHA=...

def _carregar_env() -> None:
    arquivo = Path(__file__).resolve().parent.parent / ".env"
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip())


_carregar_env()

_TOKEN_VALIDADE_S = 20 * 3600  # o token do Xano vale 24 h; renova antes
_token_servico: str = ""
_token_obtido_em: float = 0.0
_trava_token: asyncio.Lock | None = None
_trava_loop: asyncio.AbstractEventLoop | None = None


class ServicoSemCredenciais(Exception):
    """Falta HARLEY_XANO_EMAIL / HARLEY_XANO_SENHA no .env."""


async def _token_da_conta_de_servico(renovar: bool = False) -> str:
    global _token_servico, _token_obtido_em, _trava_token, _trava_loop
    loop = asyncio.get_running_loop()
    if _trava_token is None or _trava_loop is not loop:
        _trava_token, _trava_loop = asyncio.Lock(), loop
    async with _trava_token:
        if _token_servico and not renovar and time.monotonic() - _token_obtido_em < _TOKEN_VALIDADE_S:
            return _token_servico
        email, senha = os.environ.get("HARLEY_XANO_EMAIL"), os.environ.get("HARLEY_XANO_SENHA")
        if not email or not senha:
            raise ServicoSemCredenciais("Configure HARLEY_XANO_EMAIL e HARLEY_XANO_SENHA no arquivo .env")
        resposta = await _request("POST", f"{AUTH_URL}/auth/login", json={"email": email, "password": senha},
                                  autenticar=False)
        resposta.raise_for_status()
        _token_servico, _token_obtido_em = resposta.json()["authToken"], time.monotonic()
        log.info("token da conta de servico obtido")
        return _token_servico
_MAX_TENTATIVAS = 5
_ESPERA_BASE_SEGUNDOS = 1.5

# Uma conexão reaproveitada (keep-alive) em vez de uma nova a cada chamada:
# evita repetir o aperto de mão TLS com o Xano em toda consulta. Fica presa
# ao loop de eventos em que foi criada; se o loop mudar, cria outra.
_cliente: httpx.AsyncClient | None = None
_cliente_loop: asyncio.AbstractEventLoop | None = None


def _obter_cliente() -> httpx.AsyncClient:
    global _cliente, _cliente_loop
    loop = asyncio.get_running_loop()
    if _cliente is None or _cliente.is_closed or _cliente_loop is not loop:
        _cliente = httpx.AsyncClient(timeout=_TIMEOUT)
        _cliente_loop = loop
    return _cliente


def _descartar_cliente(client: httpx.AsyncClient) -> None:
    global _cliente
    if _cliente is client:
        _cliente = None
        asyncio.get_running_loop().create_task(client.aclose())


# Métodos que podem ser repetidos sem efeito colateral: o PATCH do Xano grava
# o registro completo (mesmo resultado se repetido). POST NÃO entra: repetir
# um POST que chegou ao Xano mas cuja resposta se perdeu criaria um registro
# em dobro (por exemplo, uma venda duplicada).
_REPETIVEIS = {"GET", "PATCH", "PUT", "DELETE"}


async def _request(metodo: str, url: str, *, autenticar: bool = True, **kwargs) -> httpx.Response:
    """Chamada ao Xano com retentativas. Na API de dados (BASE_URL) envia o
    token da conta de serviço e, se o Xano recusar (401), renova uma vez."""
    if autenticar and url.startswith(BASE_URL):
        cabecalhos = dict(kwargs.pop("headers", None) or {})
        try:
            cabecalhos["Authorization"] = f"Bearer {await _token_da_conta_de_servico()}"
        except ServicoSemCredenciais:
            # Sem .env: segue sem token. Com a API do Xano protegida, a chamada
            # volta 401 e o erro aparece claro no log.
            log.error("HARLEY_XANO_EMAIL/HARLEY_XANO_SENHA ausentes no .env: chamando o Xano sem login")
            return await _request(metodo, url, autenticar=False, headers=cabecalhos, **kwargs)
        resposta = await _request(metodo, url, autenticar=False, headers=cabecalhos, **kwargs)
        if resposta.status_code == 401:
            cabecalhos["Authorization"] = f"Bearer {await _token_da_conta_de_servico(renovar=True)}"
            resposta = await _request(metodo, url, autenticar=False, headers=cabecalhos, **kwargs)
        return resposta

    for tentativa in range(_MAX_TENTATIVAS):
        client = _obter_cliente()
        try:
            resposta = await client.request(metodo, url, **kwargs)
        except httpx.TransportError as erro:
            # Depois de uma queda de rede o pool de conexões pode ficar
            # inutilizável ("All connection attempts failed" mesmo com a rede
            # de volta): descarta o cliente, e a próxima chamada abre outro.
            log.warning("falha de conexao com o Xano (%s): %r", metodo, erro)
            _descartar_cliente(client)
            # rede instável / Xano demorando: tenta de novo só o que é seguro repetir
            if metodo.upper() not in _REPETIVEIS or tentativa == _MAX_TENTATIVAS - 1:
                raise
            await asyncio.sleep(_ESPERA_BASE_SEGUNDOS * (tentativa + 1))
            continue
        if resposta.status_code != 429:
            return resposta
        espera = float(resposta.headers.get("Retry-After", 0)) or _ESPERA_BASE_SEGUNDOS * (2**tentativa)
        await asyncio.sleep(min(espera, 20))
    return resposta


# Cache curto das listagens. As telas relistam as mesmas tabelas o tempo todo
# (a cada letra digitada numa busca, a cada troca de página, várias telas
# pedindo "clientes"): com o cache essas leituras são instantâneas e o limite
# de requisições do Xano Free deixa de ser atingido. Qualquer gravação feita
# pelo app (criar/atualizar/excluir) é aplicada no cache na hora (ver
# _aplicar_no_cache), então quem acabou de salvar sempre vê o dado novo. Alterações feitas por fora do
# app (painel do Xano) aparecem em no máximo _CACHE_SEGUNDOS (5 min).
_CACHE_SEGUNDOS = 300.0
_cache: dict[str, tuple[float, list[dict]]] = {}
_travas: dict[str, asyncio.Lock] = {}


def limpar_cache(tabela: str | None = None) -> None:
    if tabela is None:
        _cache.clear()
    else:
        _cache.pop(tabela, None)


async def listar(tabela: str) -> list[dict]:
    # Devolve sempre uma CÓPIA: quem chama pode alterar os dicts à vontade.
    guardado = _cache.get(tabela)
    if guardado and time.monotonic() - guardado[0] < _CACHE_SEGUNDOS:
        return copy.deepcopy(guardado[1])
    # A trava evita que várias telas pedindo a mesma tabela ao mesmo tempo
    # façam várias chamadas iguais ao Xano.
    trava = _travas.setdefault(tabela, asyncio.Lock())
    async with trava:
        guardado = _cache.get(tabela)
        if guardado and time.monotonic() - guardado[0] < _CACHE_SEGUNDOS:
            return copy.deepcopy(guardado[1])
        resposta = await _request("GET", f"{BASE_URL}/{tabela}")
        resposta.raise_for_status()
        dados = resposta.json() or []
        _cache[tabela] = (time.monotonic(), dados)
        return copy.deepcopy(dados)


async def _renovar(tabela: str) -> None:
    async with _travas.setdefault(tabela, asyncio.Lock()):
        resposta = await _request("GET", f"{BASE_URL}/{tabela}")
        resposta.raise_for_status()
        _cache[tabela] = (time.monotonic(), resposta.json() or [])


# Tabelas usadas pelas telas. Mantidas sempre em cache por manter_cache_aquecido.
TABELAS_AQUECIDAS = [
    "clientes", "produtos", "motos", "motos_clientes", "funcionarios", "fornecedores",
    "transacoes", "itens_transacao", "ordens_servico", "itens_ordem_servico",
    "entrada_mercadoria", "itens_compra_estoque",
]


async def manter_cache_aquecido() -> None:
    """Tarefa de fundo do servidor (registrada em harley_store.py): mantém as
    tabelas sempre no cache, para que nenhuma tela precise esperar o Xano.

    Primeira passada rápida ao subir (1 tabela a cada 3 s); depois renova uma
    tabela a cada 20 s, ou seja, cada tabela a cada ~3,7 min, antes de vencer o
    cache de 5 min. É 1 requisição a cada 20 s, bem abaixo do limite do plano
    Free (~10 a cada 20 s), então sobra folga para as gravações."""
    espera = 3.0
    while True:
        for tabela in TABELAS_AQUECIDAS:
            try:
                await _renovar(tabela)
            except asyncio.CancelledError:
                raise
            except Exception as erro:
                # sem internet/Xano fora: tenta de novo na próxima volta
                log.warning("cache: nao foi possivel renovar %s: %r", tabela, erro)
            await asyncio.sleep(espera)
        espera = 20.0


async def buscar(tabela: str, registro_id: int) -> dict | None:
    """Um registro pelo id. Procura na listagem em cache em vez de chamar o
    Xano uma vez por registro: as tabelas da loja são pequenas, e um
    documento de OS, por exemplo, precisava de 4 buscas avulsas, o que
    estourava o limite de requisições do plano Free (erro 429 e espera)."""
    registro_id = int(registro_id)
    return next((r for r in await listar(tabela) if r.get("id") == registro_id), None)


# Cache atualizado pela própria gravação ("write-through"). O Xano devolve o
# registro completo após criar/alterar; aplicá-lo no cache mantém a listagem
# correta SEM reler a tabela inteira. Antes, cada gravação descartava o cache
# e a tela relia produtos/vendas/itens, o que somava requisições e fazia o
# Xano Free responder 429 ("espere 20 s") durante vendas e cancelamentos.
# Se algo der errado (resposta inesperada, tabela fora do cache), descarta
# o cache da tabela, e a próxima leitura busca do Xano: nunca fica dado errado.

async def buscar_direto(tabela: str, registro_id: int) -> dict | None:
    """Um registro lido DIRETO do Xano (sem cache). Use antes de regravar o
    registro inteiro (PATCH do Xano substitui tudo): o cache pode estar até
    5 min atrasado em relação a uma alteração feita por outro processo."""
    resposta = await _request("GET", f"{BASE_URL}/{tabela}/{int(registro_id)}")
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    registro = resposta.json()
    _aplicar_no_cache(tabela, int(registro_id), registro)
    return registro


def _aplicar_no_cache(tabela: str, registro_id: int, registro: dict | None) -> None:
    guardado = _cache.get(tabela)
    if not guardado:
        return
    lista = [r for r in guardado[1] if r.get("id") != registro_id]
    if registro is not None:
        lista.append(copy.deepcopy(registro))
    _cache[tabela] = (guardado[0], lista)


async def criar(tabela: str, dados: dict) -> dict:
    try:
        resposta = await _request("POST", f"{BASE_URL}/{tabela}", json=dados)
        resposta.raise_for_status()
        registro = resposta.json()
        _aplicar_no_cache(tabela, int(registro["id"]), registro)
        return registro
    except Exception:
        limpar_cache(tabela)
        raise


async def atualizar(tabela: str, registro_id: int, dados: dict) -> dict:
    try:
        resposta = await _request("PATCH", f"{BASE_URL}/{tabela}/{registro_id}", json=dados)
        resposta.raise_for_status()
        registro = resposta.json()
        _aplicar_no_cache(tabela, int(registro_id), registro)
        return registro
    except Exception:
        limpar_cache(tabela)
        raise


async def excluir(tabela: str, registro_id: int) -> None:
    try:
        resposta = await _request("DELETE", f"{BASE_URL}/{tabela}/{registro_id}")
        if resposta.status_code != 404:
            resposta.raise_for_status()
        _aplicar_no_cache(tabela, int(registro_id), None)
    except Exception:
        limpar_cache(tabela)
        raise


class UploadIndisponivel(Exception):
    """O endpoint `motos/foto` ainda não foi criado no Xano."""


async def enviar_imagem(nome_arquivo: str, conteudo: bytes, mime: str) -> dict:
    """Sobe uma imagem para o storage do Xano e devolve o objeto de imagem
    (com `path`, `url`, etc.). Vai no campo `foto` (imagem) da tabela
    `motos`, e a `url` no campo `imagem` (texto) de produtos e motos de
    clientes. Mandar a foto direto no POST/PATCH da tabela não funciona: o
    Xano grava só o nome, sem o arquivo. O endpoint é `POST motos/foto`,
    com o arquivo no campo `arquivo` (antes o app chamava `upload/image`,
    que não existe, e o envio de fotos sempre falhava)."""
    resposta = await _request(
        "POST", f"{BASE_URL}/motos/foto", files={"arquivo": (nome_arquivo, conteudo, mime)}
    )
    if resposta.status_code == 404:
        raise UploadIndisponivel()
    resposta.raise_for_status()
    return resposta.json()


def url_da_imagem(valor: str | None) -> str:
    """Campo `imagem` (texto) de produtos/motos de clientes -> endereço para <img>.
    Fotos novas guardam a URL do Xano; as antigas, só o nome de um arquivo da
    pasta uploaded_files/ do servidor do app."""
    if not valor:
        return ""
    if valor.startswith(("http://", "https://")):
        return valor
    from reflex.config import get_config

    return f"{get_config().api_url.rstrip('/')}/_upload/{valor}"


def epoch_ms_para_datetime(valor: int | float | None) -> datetime.datetime:
    if not valor:
        return datetime.datetime.now()
    return datetime.datetime.fromtimestamp(valor / 1000)


def datetime_para_epoch_ms(valor: datetime.datetime | None = None) -> int:
    valor = valor or datetime.datetime.now()
    return int(valor.timestamp() * 1000)
