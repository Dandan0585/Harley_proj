# plataforma/acesso-ao-servidor-de-dados Specification

## Purpose
Garante que o app responda rápido e continue funcionando mesmo com as limitações do servidor de dados (lentidão, limite de requisições e quedas de rede), mostrando erros compreensíveis ao funcionário.

## Requirements

### Requirement: Telas abertas a partir de uma cópia em memória
As telas SHALL ler as tabelas de uma cópia mantida em memória no servidor do app, renovada em segundo plano, de modo que abrir uma tela não dependa de esperar o servidor de dados. Uma alteração feita fora do app, direto no servidor de dados, MUST aparecer nas telas em no máximo 5 minutos. Uma falha ao renovar a cópia MUST ser registrada no log, e a cópia anterior continua em uso até a próxima tentativa.

#### Scenario: Abrir uma tela
- **WHEN** um funcionário abre uma tela cujas tabelas já estão na cópia em memória
- **THEN** a tela é exibida sem esperar uma nova consulta ao servidor de dados

#### Scenario: Alteração feita direto no servidor de dados
- **WHEN** alguém altera um registro direto no painel do servidor de dados
- **THEN** a alteração aparece nas telas do app em até 5 minutos

### Requirement: Gravações visíveis na hora
Depois de criar, alterar ou excluir um registro pelo app, as telas SHALL mostrar o dado novo imediatamente, sem reler a tabela inteira. Se a cópia em memória não puder ser atualizada com segurança, a cópia daquela tabela MUST ser descartada, para que a próxima leitura busque os dados do servidor.

#### Scenario: Registro recém-salvo
- **WHEN** um funcionário salva um cadastro
- **THEN** o registro aparece atualizado na lista logo em seguida

### Requirement: Novas tentativas no limite de requisições
Quando o servidor de dados responder que o limite de requisições foi atingido, o sistema SHALL esperar e tentar de novo automaticamente, até 5 vezes, respeitando o tempo de espera informado pelo servidor quando houver.

#### Scenario: Limite atingido durante uma venda
- **WHEN** o servidor de dados responde "limite atingido" a uma requisição
- **THEN** o sistema espera e repete a requisição, sem que o funcionário precise refazer a operação

### Requirement: Recuperação de falhas de rede sem gravar em dobro
Em uma falha de conexão, consultas, alterações e exclusões SHALL ser tentadas de novo automaticamente. Criações de registro MUST NOT ser repetidas automaticamente, porque a primeira pode ter chegado ao servidor e a repetição criaria um registro em dobro. Depois de uma queda de rede, o sistema MUST voltar a funcionar sem que o servidor do app precise ser reiniciado.

#### Scenario: Queda de rede durante uma consulta
- **WHEN** a conexão cai durante uma consulta e volta em seguida
- **THEN** a consulta é repetida e a tela carrega normalmente

#### Scenario: Queda de rede durante uma criação
- **WHEN** a conexão cai durante a criação de um registro
- **THEN** a criação não é repetida automaticamente e o funcionário vê a mensagem de falta de conexão

#### Scenario: Rede volta depois da queda
- **WHEN** a rede volta depois de uma queda
- **THEN** as próximas operações funcionam sem reiniciar o servidor do app

### Requirement: Espera por respostas lentas
O sistema SHALL esperar até 30 segundos por uma resposta do servidor de dados antes de considerar a requisição perdida.

#### Scenario: Servidor de dados lento
- **WHEN** o servidor de dados leva 20 segundos para responder
- **THEN** a operação é concluída normalmente

### Requirement: Erros compreensíveis
Um erro inesperado em uma ação SHALL ser mostrado ao funcionário em português, com uma mensagem que diz o que fazer, e MUST ser registrado no log com os detalhes técnicos. Os casos conhecidos MUST ter mensagens próprias: servidor ocupado (limite de requisições), dados recusados ou repetidos, registro que não existe mais, falta de permissão e falta de conexão.

#### Scenario: Registro repetido
- **WHEN** o servidor de dados recusa uma gravação por dado repetido
- **THEN** aparece "Já existe um registro com esses dados (documento, placa ou chassi repetido)."

#### Scenario: Sem conexão
- **WHEN** uma ação falha por falta de conexão com o servidor de dados
- **THEN** aparece "Sem conexão com o servidor de dados. Verifique a internet e tente de novo."

#### Scenario: Erro desconhecido
- **WHEN** uma ação falha por um motivo não previsto
- **THEN** aparece uma mensagem dizendo que nada foi perdido e que a pessoa pode tentar de novo, e o erro completo fica no log
