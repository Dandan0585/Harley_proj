## Why

O grupo pediu que cada pessoa que ganha acesso ao sistema receba um e-mail de boas-vindas no e-mail cadastrado. Hoje só os clientes recebem boas-vindas: quando um administrador cria a conta de um funcionário na tela Usuários do sistema, a pessoa não é avisada de nada. O SendGrid já está configurado e foi testado em 09/10/2026, então a mudança só reaproveita o envio que existe.

## What Changes

- Ao criar uma conta na tela **Usuários do sistema**, o sistema envia à pessoa um e-mail de boas-vindas ao sistema da loja, no e-mail da conta.
- O e-mail informa que a conta foi criada, que o login é o próprio e-mail e que a senha é entregue pessoalmente por um administrador. A senha **nunca** vai no e-mail.
- A confirmação na tela passa a dizer "E-mail de boas-vindas enviado." quando o envio é colocado na fila.
- O rodapé dos e-mails passa a dizer o motivo certo do envio: "porque é cliente" nos e-mails de clientes, e "porque uma conta de acesso foi criada para você" no novo e-mail.

**Fora do escopo:**
- e-mail ao editar o e-mail de uma conta, ao trocar o perfil ou ao definir nova senha;
- campo de e-mail no cadastro de **Funcionários** (cadastro de RH, sem login): o acesso ao sistema é pela conta de usuário, e um campo novo no Xano não foi pedido;
- link do sistema no e-mail: o endereço muda entre a demonstração e a rede da loja, então o administrador informa pessoalmente;
- reenvio do e-mail para contas já existentes.

## Capabilities

### New Capabilities

- `plataforma/boas-vindas-da-conta`: e-mail de boas-vindas enviado à pessoa quando um administrador cria a conta de acesso dela.

### Modified Capabilities

Nenhuma. Os e-mails aos clientes continuam iguais; só o texto do rodapé do e-mail de cliente fica explícito, sem mudar requisito.

## Impact

- Código: `harley_store/email_clientes.py` (nova mensagem e rodapé por tipo de e-mail), `harley_store/state/usuarios_state.py` (envio após criar a conta); testes em `tests/test_fotos_e_emails.py`.
- Serviço externo: SendGrid (mesma chave e remetente do `.env`).
- Sem mudança no Xano.
