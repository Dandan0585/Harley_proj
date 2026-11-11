## Why

A loja queria se comunicar com os clientes em momentos importantes: dar as boas-vindas quando o cliente é cadastrado e parabenizá-lo quando compra uma moto, em nome da loja e pelo SendGrid.

Registro retroativo: implementado em 01/10/2026 (commit `cb9b8ff`); a ferramenta de verificação da configuração foi criada em 07/10/2026. Esta change documenta o comportamento em uso.

## What Changes

- E-mail de boas-vindas ao cadastrar um cliente com e-mail.
- E-mail de parabéns quando uma moto da loja é marcada como Vendida para um cliente com e-mail.
- Envio pelo SendGrid, em segundo plano, configurado no `.env`; sem configuração, nada é enviado e o app funciona igual.
- Ferramenta para conferir a chave, a permissão de envio e o remetente, e mandar um e-mail de teste.

## Capabilities

### New Capabilities
- `clientes/emails-aos-clientes`: e-mails automáticos enviados aos clientes em nome da loja.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: novo `harley_store/email_clientes.py`; `state/clientes_state.py` e `state/motos_loja_state.py`; novo `scripts/testar_sendgrid.py`.
- **Serviço externo**: SendGrid (API de envio); conta, chave e remetente verificado ficam por conta da loja.
- **Xano**: nenhuma mudança e nenhuma requisição a mais.
