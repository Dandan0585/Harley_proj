## ADDED Requirements

### Requirement: Telas só para administradores
As telas Painel, Clientes, Funcionários e Usuários do sistema SHALL ser usadas apenas por administradores. Os itens dessas telas MUST continuar visíveis no menu para todos os perfis. Para quem não é administrador, a tela MUST mostrar o aviso "Você precisa ser um administrador para acessar esta tela." sem nenhum dado, e o servidor MUST recusar todo evento dessas telas (carregar, buscar, salvar, excluir), mesmo que seja chamado diretamente.

#### Scenario: Funcionário abre uma tela restrita
- **WHEN** uma pessoa com o perfil Funcionário abre o Painel, Clientes, Funcionários ou Usuários do sistema
- **THEN** aparece o aviso "Você precisa ser um administrador para acessar esta tela." e nenhum dado da tela é mostrado

#### Scenario: Menu do Funcionário
- **WHEN** uma pessoa com o perfil Funcionário está logada
- **THEN** o menu lateral mostra todas as telas, inclusive Painel, Clientes, Funcionários e Usuários do sistema

#### Scenario: Evento chamado direto
- **WHEN** uma conta com o perfil Funcionário dispara um evento de uma tela restrita sem passar pela tela, como excluir um cliente
- **THEN** o servidor não executa o evento e nada é lido ou alterado no Xano

#### Scenario: Administrador abre uma tela restrita
- **WHEN** uma pessoa com o perfil Administrador abre o Painel, Clientes, Funcionários ou Usuários do sistema
- **THEN** a tela funciona como antes

#### Scenario: Cliente e funcionário em Vendas e OS
- **WHEN** uma pessoa com o perfil Funcionário registra uma venda ou uma ordem de serviço
- **THEN** ela continua podendo escolher o cliente e o funcionário responsável

### Requirement: Tela inicial por perfil
A tela inicial de cada conta SHALL depender do perfil: o Painel para o Administrador e Vendas / Balcão para o Funcionário. Essa tela MUST ser usada depois do login, ao abrir a tela de login já estando logado e no link do logo do menu lateral. Se o perfil ainda não pôde ser conferido no Xano, a conta MUST ser tratada como Funcionário.

#### Scenario: Login de Funcionário
- **WHEN** uma pessoa com o perfil Funcionário entra no sistema
- **THEN** ela é levada para Vendas / Balcão

#### Scenario: Login de Administrador
- **WHEN** uma pessoa com o perfil Administrador entra no sistema
- **THEN** ela é levada para o Painel

#### Scenario: Logo do menu
- **WHEN** uma pessoa com o perfil Funcionário clica no logo do menu lateral
- **THEN** ela vai para Vendas / Balcão

## MODIFIED Requirements

### Requirement: Administração de contas só para administradores
A tela "Usuários do sistema" SHALL ser usada apenas por administradores, conforme o requisito "Telas só para administradores". Além disso, o servidor de dados MUST recusar as operações de administração feitas por quem não é administrador, mesmo que a pessoa chame a API diretamente.

#### Scenario: Funcionário abre a tela de usuários
- **WHEN** uma pessoa com o perfil Funcionário abre o endereço da tela Usuários
- **THEN** aparece o aviso "Você precisa ser um administrador para acessar esta tela." e nenhuma conta é listada

#### Scenario: Chamada direta à API de administração
- **WHEN** uma conta com o perfil Funcionário chama diretamente um endpoint de administração de contas
- **THEN** o servidor de dados recusa a operação com o status de acesso negado
