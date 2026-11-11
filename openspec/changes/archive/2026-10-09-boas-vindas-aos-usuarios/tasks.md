## 1. Envio do e-mail

- [x] 1.1 Adicionar a `_modelo_html` o parâmetro do motivo do rodapé (padrão: cliente) e criar `boas_vindas_conta(nome, email)` em `harley_store/email_clientes.py` (design D1 e D2); verificar com teste automático que o e-mail vai ao endereço da conta, escapa o nome, tem o rodapé de conta e não contém a senha
- [x] 1.2 Chamar `boas_vindas_conta` em `UsuariosState.salvar` só depois de a conta ser criada, e acrescentar "E-mail de boas-vindas enviado." à confirmação quando o envio for colocado na fila (design D3); verificar com teste automático que a conta recusada pelo Xano não envia e-mail e que, sem configuração, a conta é criada sem envio
- [x] 1.3 Rodar todos os testes e `reflex compile --dry`; verificar que passam

## 2. Verificação e documentação

- [x] 2.1 Enviar pelo SendGrid real um e-mail de boas-vindas de conta para o endereço remetente da loja; verificar que o SendGrid aceita (HTTP 202)
- [x] 2.2 Atualizar no README as seções "Contas, perfis e senhas" e "E-mails aos clientes (SendGrid)"; verificar lendo as seções
