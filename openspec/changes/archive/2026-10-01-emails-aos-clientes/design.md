## Context

Motivação em proposal.md. O app roda num servidor próprio (Reflex) e já guarda segredos no `.env`. O Xano Free é limitado em requisições, e a equipe pediu para não sobrecarregar o banco. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Enviar sem tocar no Xano e sem atrasar o funcionário.

**Non-Goals:**
- Campanhas de marketing ou envio em massa.
- Histórico dos e-mails enviados no banco.
- E-mail para vendas lançadas na tela de Vendas.

## Decisions

### D1. SendGrid chamado pelo servidor do app
`email_clientes.py` chama a API v3 do SendGrid (`/mail/send`) com `httpx`, usando `SENDGRID_API_KEY`, `SENDGRID_REMETENTE` e `SENDGRID_REMETENTE_NOME` do `.env`.
- *Alternativa:* endpoint no Xano. Rejeitada: mais requisições no plano Free e a chave ficaria em outro lugar.

### D2. Segundo plano
O envio é uma tarefa `asyncio` guardada num conjunto (para não ser descartada antes de terminar); a função devolve na hora se o e-mail entrou na fila, para a tela confirmar.

### D3. Quando disparar
Boas-vindas: só na criação de cliente com e-mail. Parabéns: no `salvar` da moto, quando a situação passa a Vendida ou o comprador muda (o state guarda a situação e o cliente lidos ao abrir a edição).

### D4. Modelo de e-mail
HTML com tabelas e estilos embutidos (o que os programas de e-mail entendem), cores de `components/tema.py`, textos do cliente passados por `html.escape`, e versão em texto simples.

### D5. Ferramenta de verificação
`scripts/testar_sendgrid.py` consulta `/scopes` (permissão `mail.send`) e `/verified_senders`, e envia o teste só se a pessoa digitar um endereço.

## Risks / Trade-offs

- [Período de teste do SendGrid termina em 06/12/2026] → Depois disso, sem plano pago, os envios são recusados; o app continua funcionando e o erro fica no log.
- [Remetente @gmail.com cai no spam] → Recomendado usar o endereço do domínio da loja.
- [Configuração ainda não concluída] → Em 07/10/2026 a ferramenta de verificação recusou a chave configurada (era o ID da chave, não a chave); o envio real depende de a loja colar a chave correta no `.env`.
