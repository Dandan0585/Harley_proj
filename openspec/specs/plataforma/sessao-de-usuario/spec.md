# plataforma/sessao-de-usuario Specification

## Purpose
Define quando uma pessoa está de fato logada no Harley Store: a sessão só vale com um token aceito pelo servidor de dados, a identidade vem do servidor e nenhuma ação protegida roda sem sessão válida.

## Requirements

### Requirement: Sessão conferida no servidor de dados
O acesso às páginas protegidas SHALL exigir um token aceito pelo servidor de dados (Xano). A simples existência do cookie MUST NOT bastar: token inválido, vencido, forjado ou de conta excluída MUST levar à tela de login.

#### Scenario: Token válido
- **WHEN** uma pessoa com token aceito pelo servidor de dados abre uma página protegida
- **THEN** a página é exibida normalmente

#### Scenario: Cookie inventado ou vencido
- **WHEN** o navegador tem um cookie de token que o servidor de dados recusa
- **THEN** a sessão é encerrada e a pessoa é levada à tela de login

#### Scenario: Conta excluída durante o uso
- **WHEN** a conta de quem está logado é excluída ou tem o token recusado pelo servidor de dados
- **THEN** essa pessoa perde o acesso em até 10 minutos, na próxima conferência da sessão

### Requirement: Identidade vinda do servidor
A identidade do usuário logado (id, nome e perfil) SHALL ser obtida do servidor de dados a partir do token. O sistema MUST NOT usar como identidade valores guardados em cookies que a pessoa possa editar no navegador.

#### Scenario: Cookie de identidade editado
- **WHEN** alguém altera no navegador um cookie com nome ou id de usuário
- **THEN** o sistema continua usando a identidade devolvida pelo servidor de dados para aquele token

#### Scenario: Nome exibido no menu
- **WHEN** uma pessoa entra no sistema
- **THEN** o menu lateral mostra o nome da conta conferida no servidor de dados

### Requirement: Validade da sessão
O cookie da sessão SHALL vencer junto com o token do servidor de dados (24 horas). Ao sair, a sessão MUST ser encerrada no navegador.

#### Scenario: Sessão de mais de 24 horas
- **WHEN** passam 24 horas desde o login
- **THEN** o cookie da sessão deixa de existir e a pessoa precisa entrar de novo

#### Scenario: Sair
- **WHEN** a pessoa clica em "Sair"
- **THEN** a sessão é encerrada e a tela de login é exibida

### Requirement: Ações protegidas no servidor
Toda ação das telas protegidas (salvar, excluir, cancelar, carregar dados) SHALL ser recusada no servidor quando não houver sessão válida, inclusive quando a ação for enviada diretamente ao servidor sem abrir a página.

#### Scenario: Ação sem sessão
- **WHEN** uma ação de uma tela protegida chega ao servidor sem sessão válida
- **THEN** a ação não é executada, a pessoa recebe o aviso "Sua sessão expirou. Entre novamente." e é levada à tela de login

### Requirement: Servidor de dados indisponível
Quando o servidor de dados não responder no momento da conferência, o sistema SHALL mostrar uma mensagem clara e MUST NOT tratar a pessoa como deslogada nem como logada indevidamente.

#### Scenario: Pessoa já conferida e servidor fora do ar
- **WHEN** a conferência periódica falha por falta de conexão e o token já tinha sido aceito nesta sessão
- **THEN** a pessoa continua trabalhando normalmente

#### Scenario: Primeira conferência com servidor fora do ar
- **WHEN** o token ainda não foi conferido nesta sessão e o servidor de dados não responde
- **THEN** a ação não é executada e aparece a mensagem de que não foi possível confirmar o login por falta de conexão, sem levar à tela de login

### Requirement: Página de login para quem já entrou
Quem já tem sessão válida e abre a página de login SHALL ser levado diretamente ao Painel.

#### Scenario: Abrir o login já logado
- **WHEN** uma pessoa com sessão válida abre a página de login
- **THEN** ela é redirecionada para o Painel
