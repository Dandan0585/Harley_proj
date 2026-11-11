"""
E-mails automáticos da loja, enviados pelo SendGrid (https://sendgrid.com).

- Boas-vindas: quando um cliente com e-mail é cadastrado (tela Clientes).
- Parabéns pela compra: quando uma moto da loja é marcada como "Vendida"
  para um cliente com e-mail (Produtos > Motos ou venda no Balcão).
- Boas-vindas à conta: quando um administrador cria uma conta de acesso
  (tela Usuários do sistema). A senha nunca vai no e-mail.
- Pagamento confirmado: quando o Asaas confirma o pagamento da cobrança de
  uma venda (pagamentos_servico.py). Sai uma única vez por venda.

O envio sai do servidor do app direto para o SendGrid: não grava nada no
Xano e não gasta requisições dele. É feito em segundo plano, então o
cadastro não espera o e-mail; uma falha no envio fica só no log e nunca
desfaz o cadastro ou a venda.

Configuração, no arquivo .env da pasta do projeto (fora do git):
    SENDGRID_API_KEY=SG.xxxxx            (Settings > API Keys, permissão "Mail Send")
    SENDGRID_REMETENTE=contato@sualoja.com.br   (remetente verificado no SendGrid)
    SENDGRID_REMETENTE_NOME=Harley Store        (opcional)
Sem SENDGRID_API_KEY / SENDGRID_REMETENTE, nada é enviado (o app funciona igual).
"""

from __future__ import annotations

import asyncio
import html
import logging
import os

import httpx

from .components.tema import BORDA, LARANJA as _LARANJA, PRETO, PRETO_CARTAO

log = logging.getLogger("harley_store.email")

_URL_SENDGRID = "https://api.sendgrid.com/v3/mail/send"

# referências às tarefas em andamento (sem isso o asyncio pode descartá-las no meio)
_tarefas: set[asyncio.Task] = set()


def configurado() -> bool:
    return bool(os.environ.get("SENDGRID_API_KEY") and os.environ.get("SENDGRID_REMETENTE"))


def _nome_loja() -> str:
    return os.environ.get("SENDGRID_REMETENTE_NOME") or "Harley Store"


def nome_loja() -> str:
    return _nome_loja()


def _primeiro_nome(nome: str) -> str:
    return (nome or "").split(" ")[0] or "cliente"


def _modelo_html(titulo: str, paragrafos: list[str], motivo: str = "é cliente da {loja}") -> str:
    """Corpo do e-mail com a cara da loja (tabelas e estilos inline, que é o
    que os programas de e-mail entendem). Os textos já vêm escapados.
    `motivo` completa o rodapé "Você recebeu este e-mail porque ..."."""
    loja = html.escape(_nome_loja())
    motivo = motivo.format(loja=loja)
    corpo = "".join(
        f'<p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:#e6e6e6">{p}</p>' for p in paragrafos
    )
    return f"""<!doctype html>
<html lang="pt-BR"><body style="margin:0;background:{PRETO};font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PRETO};padding:24px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:{PRETO_CARTAO};border:1px solid {BORDA};border-radius:10px">
<tr><td style="padding:22px 28px;border-bottom:3px solid {_LARANJA}">
<span style="font-size:20px;font-weight:bold;letter-spacing:2px;color:#ffffff">{loja.upper()}</span>
</td></tr>
<tr><td style="padding:28px">
<h1 style="margin:0 0 18px;font-size:22px;color:#ffffff">{titulo}</h1>
{corpo}
<p style="margin:24px 0 0;font-size:16px;color:#e6e6e6">Um abraço,<br><strong style="color:{_LARANJA}">Equipe {loja}</strong></p>
</td></tr>
</table>
<p style="font-size:12px;color:#777;margin:14px 0 0">Você recebeu este e-mail porque {motivo}.</p>
</td></tr></table>
</body></html>"""


async def _enviar(para: str, nome: str, assunto: str, corpo_html: str, corpo_texto: str) -> None:
    dados = {
        "personalizations": [{"to": [{"email": para, "name": nome}]}],
        "from": {"email": os.environ["SENDGRID_REMETENTE"], "name": _nome_loja()},
        "subject": assunto,
        "content": [
            {"type": "text/plain", "value": corpo_texto},
            {"type": "text/html", "value": corpo_html},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as cliente:
            resposta = await cliente.post(
                _URL_SENDGRID, json=dados,
                headers={"Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}"},
            )
        if resposta.status_code >= 400:
            # 401/403: chave inválida ou sem permissão; 403 também se o remetente não foi verificado
            log.error("SendGrid recusou o e-mail \"%s\" (HTTP %s): %s", assunto, resposta.status_code, resposta.text[:300])
        else:
            log.info("e-mail \"%s\" enviado", assunto)
    except Exception:
        log.exception("falha ao enviar o e-mail \"%s\" pelo SendGrid", assunto)


def _agendar(para: str, nome: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
    """Dispara o envio em segundo plano. True se o e-mail foi colocado na fila."""
    if not configurado() or not para:
        return False
    tarefa = asyncio.get_running_loop().create_task(_enviar(para, nome, assunto, corpo_html, corpo_texto))
    _tarefas.add(tarefa)
    tarefa.add_done_callback(_tarefas.discard)
    return True


def boas_vindas(nome: str, email: str) -> bool:
    primeiro = _primeiro_nome(nome)
    loja = _nome_loja()
    paragrafos = [
        f"Olá, {html.escape(primeiro)}! Seu cadastro na {html.escape(loja)} foi concluído e é um prazer ter você com a gente.",
        "Aqui você encontra motos Harley-Davidson, peças originais, acessórios, vestuário e uma oficina "
        "preparada para cuidar da sua moto em cada revisão.",
        "Precisando de qualquer coisa, é só chamar a nossa equipe. Bem-vindo(a) à família!",
    ]
    texto = (f"Olá, {primeiro}! Seu cadastro na {loja} foi concluído e é um prazer ter você com a gente.\n\n"
             "Aqui você encontra motos Harley-Davidson, peças originais, acessórios, vestuário e uma oficina "
             "preparada para cuidar da sua moto em cada revisão.\n\n"
             f"Precisando de qualquer coisa, é só chamar a nossa equipe. Bem-vindo(a) à família!\n\nEquipe {loja}")
    return _agendar(email, nome, f"Bem-vindo(a) à {loja}, {primeiro}!",
                    _modelo_html("Bem-vindo(a) à família!", paragrafos), texto)


def boas_vindas_conta(nome: str, email: str) -> bool:
    """Boas-vindas a quem ganhou uma conta de acesso ao sistema (tela Usuários
    do sistema). Não recebe a senha de propósito: ela nunca vai por e-mail."""
    primeiro = _primeiro_nome(nome)
    loja = _nome_loja()
    paragrafos = [
        f"Olá, {html.escape(primeiro)}! Sua conta de acesso ao sistema da {html.escape(loja)} foi criada.",
        f'Para entrar, use este e-mail (<strong style="color:{_LARANJA}">{html.escape(email)}</strong>) '
        "e a senha que um administrador vai entregar a você pessoalmente.",
        "No sistema você registra vendas, ordens de serviço, compras e cadastros, e acompanha o painel da loja. "
        "Seja bem-vindo(a) à equipe!",
    ]
    texto = (f"Olá, {primeiro}! Sua conta de acesso ao sistema da {loja} foi criada.\n\n"
             f"Para entrar, use este e-mail ({email}) e a senha que um administrador vai entregar a você "
             "pessoalmente.\n\n"
             "No sistema você registra vendas, ordens de serviço, compras e cadastros, e acompanha o painel da "
             f"loja. Seja bem-vindo(a) à equipe!\n\nEquipe {loja}")
    return _agendar(email, nome, f"Bem-vindo(a) à equipe {loja}, {primeiro}!",
                    _modelo_html("Sua conta foi criada", paragrafos,
                                 motivo="uma conta de acesso ao sistema da {loja} foi criada para você"),
                    texto)


def parabens_compra(nome: str, email: str, moto: str) -> bool:
    """`moto`: descrição da moto comprada, ex.: "Harley-Davidson Fat Boy 114 2025 Vivid Black"."""
    primeiro = _primeiro_nome(nome)
    loja = _nome_loja()
    paragrafos = [
        f"Parabéns, {html.escape(primeiro)}! Você acaba de adquirir a sua "
        f'<strong style="color:{_LARANJA}">{html.escape(moto)}</strong>.',
        "Obrigado por escolher a gente para esse momento. Agora é aproveitar cada quilômetro.",
        "Conte conosco para revisões, peças, acessórios e o que mais a sua moto precisar.",
    ]
    texto = (f"Parabéns, {primeiro}! Você acaba de adquirir a sua {moto}.\n\n"
             "Obrigado por escolher a gente para esse momento. Agora é aproveitar cada quilômetro.\n\n"
             f"Conte conosco para revisões, peças, acessórios e o que mais a sua moto precisar.\n\nEquipe {loja}")
    return _agendar(email, nome, f"Parabéns pela sua {moto}!",
                    _modelo_html("Parabéns pela sua nova moto!", paragrafos), texto)


def _moeda(valor: float) -> str:
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pagamento_confirmado(nome: str, email: str, venda_id: int, valor: float, forma: str, data: str) -> bool:
    """Confirmação do pagamento de uma venda cobrada pelo Asaas. `forma`: texto
    da forma ("Boleto"...); `data`: data do pagamento já formatada (DD/MM/AAAA)."""
    primeiro = _primeiro_nome(nome)
    loja = _nome_loja()
    valor_txt = f"R$ {_moeda(valor)}"
    detalhes = [("Venda", f"nº {int(venda_id)}"), ("Valor pago", valor_txt), ("Forma de pagamento", forma),
                ("Data do pagamento", data or "—")]
    tabela = "".join(
        f'<tr><td style="padding:6px 0;color:#9a9a9a;font-size:14px">{html.escape(r)}</td>'
        f'<td style="padding:6px 0 6px 16px;color:#ffffff;font-size:15px;font-weight:bold">{html.escape(v)}</td></tr>'
        for r, v in detalhes
    )
    paragrafos = [
        f"Olá, {html.escape(primeiro)}! Recebemos o pagamento da sua compra na {html.escape(loja)}. Obrigado!",
        f'<table role="presentation" cellpadding="0" cellspacing="0">{tabela}</table>',
        "Guarde este e-mail como comprovante. Qualquer dúvida, é só falar com a nossa equipe.",
    ]
    texto = (f"Olá, {primeiro}! Recebemos o pagamento da sua compra na {loja}. Obrigado!\n\n"
             + "\n".join(f"{r}: {v}" for r, v in detalhes)
             + "\n\nGuarde este e-mail como comprovante. Qualquer dúvida, é só falar com a nossa equipe."
             + f"\n\nEquipe {loja}")
    return _agendar(email, nome, f"Pagamento confirmado - venda nº {int(venda_id)}",
                    _modelo_html("Pagamento confirmado!", paragrafos, motivo="fez uma compra na {loja}"),
                    texto)
