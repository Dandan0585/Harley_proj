# plataforma/acesso-em-rede-local Specification

## Purpose
Garante que o Harley Store fique disponível para os funcionários da loja a partir de qualquer aparelho da rede interna, durante todo o expediente, sem ser afetado pelo desenvolvimento feito no mesmo computador.

## Requirements

### Requirement: Acesso pelos aparelhos da rede interna
O sistema de produção SHALL poder ser usado a partir de qualquer computador ou celular conectado à rede interna da loja, por meio de um endereço fixo do computador servidor. O uso inclui abrir as telas e também executar ações, como entrar e registrar dados.

#### Scenario: Outro computador da rede usa o sistema
- **WHEN** um funcionário, em outro computador da rede interna, abre no navegador o endereço de produção do sistema
- **THEN** a tela inicial é exibida
- **AND** ele consegue entrar com seu email e senha e navegar pelas telas, sem erro de conexão

#### Scenario: Celular na rede da loja usa o sistema
- **WHEN** um celular conectado ao Wi-Fi da loja abre o endereço de produção
- **THEN** o sistema carrega e responde às ações da mesma forma que no computador servidor

#### Scenario: Endereço estável
- **WHEN** o computador servidor é reiniciado ou se reconecta ao Wi-Fi
- **THEN** o sistema continua disponível no mesmo endereço de produção

### Requirement: Exposição restrita à rede privada da loja
O sistema de produção MUST aceitar conexões de outros aparelhos apenas quando o computador servidor estiver em uma rede classificada como Privada. O ambiente de desenvolvimento MUST NOT aceitar conexões de outros aparelhos.

#### Scenario: Rede pública não expõe o sistema
- **WHEN** o computador servidor está conectado a uma rede classificada como Pública
- **THEN** outros aparelhos dessa rede não conseguem acessar as portas do sistema

#### Scenario: Desenvolvimento não é acessível pela rede
- **WHEN** outro aparelho da rede interna tenta abrir o endereço do ambiente de desenvolvimento
- **THEN** a conexão é recusada

### Requirement: Disponibilidade durante o expediente
O sistema de produção SHALL permanecer disponível diariamente das 7h às 19h, janela que cobre o expediente da loja (segunda a sexta das 8h às 18h; sábado e domingo das 9h às 16h) com uma hora de folga. Nessa janela, o computador servidor MUST NOT entrar em suspensão por inatividade nem reiniciar automaticamente para atualizações.

#### Scenario: Servidor ocioso não derruba o sistema
- **WHEN** ninguém usa o computador servidor por mais de 15 minutos, estando ele ligado na tomada
- **THEN** o sistema continua acessível pelos outros aparelhos

#### Scenario: Tampa fechada não derruba o sistema
- **WHEN** a tampa do notebook servidor é fechada, estando ele ligado na tomada
- **THEN** o sistema continua acessível pelos outros aparelhos

#### Scenario: Atualização do Windows fora do expediente
- **WHEN** o Windows precisa reiniciar para concluir uma atualização
- **THEN** o reinício automático só ocorre fora da janela das 7h às 19h

### Requirement: Retorno automático após reinício
O sistema de produção SHALL voltar a funcionar sozinho sempre que o computador servidor for ligado ou reiniciado, sem que alguém precise abrir um terminal ou executar comandos.

#### Scenario: Reinício do computador
- **WHEN** o computador servidor é reiniciado
- **THEN** depois da inicialização o sistema de produção fica acessível pelos outros aparelhos, sem intervenção manual

#### Scenario: Terminal fechado não derruba o sistema
- **WHEN** alguém fecha janelas ou terminais abertos no computador servidor
- **THEN** o sistema de produção continua em execução

### Requirement: Produção isolada do desenvolvimento
O ambiente de produção SHALL executar uma versão do sistema registrada no controle de versão, em uma pasta própria e separada da pasta de desenvolvimento. Alterações no desenvolvimento MUST NOT afetar a produção até que a produção seja atualizada de forma deliberada.

#### Scenario: Edição de código não afeta os funcionários
- **WHEN** um arquivo do sistema é alterado ou o ambiente de desenvolvimento é iniciado ou parado
- **THEN** o ambiente de produção continua em execução, com o mesmo comportamento, sem desconectar os usuários

#### Scenario: Dois ambientes ao mesmo tempo
- **WHEN** os ambientes de produção e de desenvolvimento estão em execução simultaneamente no mesmo computador
- **THEN** cada um responde em suas próprias portas, sem conflito

### Requirement: Atualização controlada da produção
A produção SHALL ser atualizada apenas por um roteiro documentado, que leva para ela uma versão já registrada no controle de versão. Após a atualização, a produção MUST executar exatamente essa versão, e o roteiro MUST permitir voltar à versão anterior.

#### Scenario: Publicar uma nova versão
- **WHEN** uma alteração é registrada no controle de versão e o roteiro de atualização é executado
- **THEN** a produção passa a executar a nova versão, e os funcionários voltam a usar o sistema no mesmo endereço

#### Scenario: Alteração não registrada não chega à produção
- **WHEN** existem alterações no desenvolvimento que ainda não foram registradas no controle de versão
- **THEN** o roteiro de atualização não as leva para a produção

#### Scenario: Voltar à versão anterior
- **WHEN** a nova versão apresenta um problema
- **THEN** é possível retornar a produção à versão anterior seguindo o roteiro documentado
