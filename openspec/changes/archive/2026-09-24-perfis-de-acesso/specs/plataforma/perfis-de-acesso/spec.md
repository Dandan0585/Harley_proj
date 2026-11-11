## Purpose

Separa quem administra as contas de login (Administrador) de quem apenas usa o sistema no dia a dia (Funcionário), com as regras aplicadas no servidor de dados.

## ADDED Requirements

### Requirement: Dois perfis de acesso
Cada conta de login SHALL ter um de dois perfis: Administrador ou Funcionário. Contas novas MUST ser criadas com o perfil Funcionário.

#### Scenario: Conta recém-criada
- **WHEN** um administrador cria uma conta
- **THEN** a conta aparece na lista com o perfil Funcionário

### Requirement: Administração de contas só para administradores
A tela "Usuários do sistema" SHALL ser usada apenas por administradores. O item do menu MUST ficar oculto para Funcionários, a tela MUST mostrar um aviso de falta de permissão para quem não é administrador, e o servidor de dados MUST recusar as operações de administração feitas por quem não é administrador, mesmo que a pessoa chame a API diretamente.

#### Scenario: Funcionário abre a tela de usuários
- **WHEN** uma pessoa com o perfil Funcionário abre o endereço da tela Usuários
- **THEN** aparece o aviso de que a tela é só para administradores e nenhuma conta é listada

#### Scenario: Chamada direta à API de administração
- **WHEN** uma conta com o perfil Funcionário chama diretamente um endpoint de administração de contas
- **THEN** o servidor de dados recusa a operação com o status de acesso negado

### Requirement: Operações do administrador
O administrador SHALL poder criar contas (nome, e-mail e senha com confirmação), trocar o e-mail de uma conta, definir uma nova senha, mudar o perfil e excluir contas. O e-mail MUST ser válido e não pode ser usado por outra conta, e a senha MUST ter pelo menos 8 caracteres, com letras e números.

#### Scenario: E-mail já usado
- **WHEN** o administrador tenta criar uma conta ou trocar um e-mail para um endereço que outra conta já usa
- **THEN** a operação é recusada com a mensagem de que o e-mail já é usado

#### Scenario: Senha fraca
- **WHEN** o administrador define uma senha sem números ou com menos de 8 caracteres
- **THEN** a senha é recusada com a mensagem "A senha precisa ter pelo menos 8 caracteres, com letras e números."

### Requirement: Proteção contra ficar sem acesso
O administrador MUST NOT poder alterar o próprio perfil nem excluir a própria conta, e o sistema MUST NOT permitir excluir a única conta existente.

#### Scenario: Excluir a própria conta
- **WHEN** o administrador tenta excluir a conta com a qual está logado
- **THEN** aparece "Você não pode excluir a própria conta." e nada é alterado

#### Scenario: Alterar o próprio perfil
- **WHEN** o administrador tenta mudar o próprio perfil
- **THEN** aparece "Você não pode alterar o próprio perfil." e nada é alterado

### Requirement: Sem cadastro público nem troca de senha sem confirmação
A tela de login MUST NOT oferecer a criação de contas. A senha de uma conta SHALL ser redefinida somente por um administrador; a opção "Esqueci minha senha" MUST orientar a pessoa a procurar um administrador.

#### Scenario: Esqueci minha senha
- **WHEN** uma pessoa escolhe "Esqueci minha senha" na tela de login
- **THEN** aparece a orientação de que, por segurança, a senha só pode ser redefinida por um administrador do sistema
