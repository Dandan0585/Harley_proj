# plataforma/protecao-da-api-de-dados Specification

## Purpose
Impede o acesso aos dados da loja sem login e define como o servidor do app se autentica no servidor de dados com uma conta de serviço, incluindo o reparo dessa conta.

## Requirements

### Requirement: API de dados exige login
Todos os endpoints de dados da loja SHALL exigir um token de login válido. Uma requisição sem token ou com token inválido MUST ser recusada, sem devolver nem alterar dados.

#### Scenario: Requisição sem login
- **WHEN** alguém chama um endpoint de dados, como a lista de clientes, sem token
- **THEN** o servidor de dados responde que é necessário autenticar-se (401) e nenhum dado é devolvido

### Requirement: Conta de serviço do app
O servidor do app SHALL acessar os dados com uma conta de serviço própria, e não com a conta do funcionário logado. As credenciais dessa conta MUST ficar no arquivo de configuração de cada instalação (`.env`), fora do controle de versão, e MUST NOT aparecer nas telas nem no log.

#### Scenario: Funcionário usa o sistema
- **WHEN** um funcionário logado abre uma tela
- **THEN** os dados são lidos pelo servidor do app com a conta de serviço, e a identidade do funcionário continua sendo conferida à parte

#### Scenario: Credenciais ausentes
- **WHEN** o arquivo `.env` não tem as credenciais da conta de serviço
- **THEN** o log registra que elas estão ausentes, e as telas mostram que não há permissão para a operação

### Requirement: Renovação do token da conta de serviço
O token da conta de serviço SHALL ser renovado antes de vencer. Se o servidor de dados recusar o token, o sistema MUST obter um token novo e repetir a chamada uma vez.

#### Scenario: Token recusado
- **WHEN** o servidor de dados recusa o token da conta de serviço em uma chamada
- **THEN** o sistema faz um novo login da conta de serviço e repete a chamada

### Requirement: Reparo da conta de serviço
O sistema SHALL oferecer um procedimento, executado com o login de um administrador, que gera uma senha nova e forte para a conta de serviço, grava essa senha no servidor de dados e no `.env` do desenvolvimento e, com confirmação, no da produção, recria a conta se ela não existir e confere que ela consegue ler os dados. A senha gerada MUST NOT ser exibida.

#### Scenario: Senha da conta de serviço recusada
- **WHEN** todas as telas mostram falta de permissão porque a senha da conta de serviço deixou de valer, e um administrador executa o procedimento de reparo
- **THEN** a conta de serviço recebe uma senha nova, o `.env` é atualizado, e o procedimento informa quantos clientes conseguiu ler

#### Scenario: Login de administrador incorreto
- **WHEN** o e-mail ou a senha de administrador informados no procedimento estão errados
- **THEN** o procedimento avisa e nada é alterado
