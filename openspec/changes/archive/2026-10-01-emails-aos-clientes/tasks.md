## 1. Envio

- [x] 1.1 Criar `email_clientes.py` com os e-mails de boas-vindas e de parabéns, envio em segundo plano e modelo com a identidade da loja; feito em 01/10/2026 (commit `cb9b8ff`) e verificado pelos testes `test_envia_para_o_sendgrid` (endereço, destinatário, assunto e texto escapado) e `test_sem_configuracao_nao_envia`
- [x] 1.2 Disparar as boas-vindas no cadastro de cliente com e-mail; verificado no código de `clientes_state.py`
- [x] 1.3 Disparar os parabéns quando a moto passa a Vendida ou muda de comprador; verificado no código de `motos_loja_state.py` (`_status_lido` e `_cliente_lido`)
- [x] 1.4 Documentar a configuração no README (seção "E-mails aos clientes (SendGrid)"); verificado em 07/10/2026

## 2. Verificação da configuração

- [x] 2.1 Criar `scripts/testar_sendgrid.py` (configuração, chave, permissão, remetente e e-mail de teste, sem mostrar a chave); feito em 07/10/2026 e verificado contra a conta real: ele acusou a falta de configuração e, depois, a chave recusada

Observação: o envio real ainda não foi confirmado, porque a chave do SendGrid configurada em 07/10/2026 não era válida. Quando a loja colar a chave correta, `scripts/testar_sendgrid.py` confirma o envio.
