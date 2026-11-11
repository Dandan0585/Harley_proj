## Purpose

Avisa por e-mail a pessoa que ganhou acesso ao sistema da loja, quando um administrador cria a conta dela, sem nunca enviar a senha.

## ADDED Requirements

### Requirement: E-mail de boas-vindas ao criar a conta
Quando um administrador criar uma conta de acesso, o sistema SHALL enviar à pessoa, no e-mail da conta, um e-mail de boas-vindas em nome da loja. A confirmação na tela MUST informar que o e-mail foi enviado. Editar o e-mail, o perfil ou a senha de uma conta existente MUST NOT enviar o e-mail.

#### Scenario: Conta nova
- **WHEN** um administrador cria a conta de "Ana Souza" com o e-mail ana@exemplo.com e o envio está configurado
- **THEN** a conta é criada, a tela informa "E-mail de boas-vindas enviado." e ana@exemplo.com recebe o e-mail de boas-vindas

#### Scenario: Conta existente alterada
- **WHEN** um administrador troca o e-mail ou o perfil de uma conta existente
- **THEN** nenhum e-mail de boas-vindas é enviado

#### Scenario: Conta não criada
- **WHEN** a criação da conta é recusada (por exemplo, e-mail já cadastrado)
- **THEN** nenhum e-mail é enviado

### Requirement: Conteúdo sem a senha
O e-mail SHALL informar que a conta foi criada e que o login é o e-mail da conta, e SHALL orientar que a senha é entregue pessoalmente por um administrador. O e-mail MUST NOT conter a senha. O nome da pessoa MUST ser tratado como texto, e o rodapé MUST explicar que o e-mail foi enviado porque uma conta de acesso foi criada.

#### Scenario: Senha fora do e-mail
- **WHEN** a conta é criada com uma senha
- **THEN** nem o assunto nem o corpo do e-mail contêm a senha

#### Scenario: Nome com caracteres especiais
- **WHEN** o nome da conta contém sinais como "<" e ">"
- **THEN** o nome aparece no e-mail como texto, sem alterar a formatação da mensagem

### Requirement: Criação da conta independente do e-mail
O envio SHALL acontecer em segundo plano. Uma falha no envio MUST NOT desfazer a criação da conta e MUST ficar registrada no log. Sem a chave e o remetente configurados, a conta MUST ser criada normalmente, sem e-mail e sem erro.

#### Scenario: Envio não configurado
- **WHEN** um administrador cria uma conta e o SendGrid não está configurado
- **THEN** a conta é criada, nenhum e-mail é enviado e a tela não informa envio
