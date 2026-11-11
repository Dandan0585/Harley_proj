## Purpose

Registra os serviços da oficina: a ordem de serviço liga uma moto de cliente a um mecânico e reúne as peças usadas e a mão de obra, com o acompanhamento da situação.

## ADDED Requirements

### Requirement: Abertura da ordem de serviço
Uma ordem de serviço SHALL ser aberta para uma moto de cliente cadastrada e um mecânico (funcionário do tipo Mecânico), com a situação inicial ABERTA e a data e hora de abertura.

#### Scenario: Sem moto ou sem mecânico
- **WHEN** não há moto de cliente ou funcionário do tipo Mecânico cadastrado
- **THEN** a tela pede para cadastrar primeiro e não abre a OS

### Requirement: Peças e serviços na mesma OS
A OS SHALL aceitar peças do estoque (produto, quantidade e valor) e serviços de mão de obra (descrição e valor). Ao escolher a peça, o valor MUST ser sugerido como preço de venda vezes a quantidade e pode ser alterado. Serviços MUST NOT movimentar o estoque. A descrição do serviço é obrigatória e nenhum valor pode ser negativo.

#### Scenario: OS com peça e mão de obra
- **WHEN** o funcionário lança uma bateria de R$ 220,00 e o serviço "troca de bateria" de R$ 250,00 e abre a OS
- **THEN** a OS é gravada com os dois itens, o valor total é R$ 470,00 e só a bateria sai do estoque

#### Scenario: Serviço sem descrição
- **WHEN** o funcionário tenta adicionar um serviço sem descrição
- **THEN** o serviço não é adicionado e aparece o pedido para descrever o serviço

### Requirement: Valor da OS
O valor de uma OS SHALL ser a soma dos valores das peças e dos serviços lançados, exibido na lista de ordens de serviço junto com a moto, o mecânico, a situação e o número de itens.

#### Scenario: Lista de ordens
- **WHEN** o funcionário abre a tela Ordens de serviço
- **THEN** cada OS aparece com a data de abertura, a moto, o mecânico, a situação, o número de itens e o valor total

### Requirement: Situações da OS
A OS SHALL ter uma das situações ABERTA, EM_ANDAMENTO, CONCLUIDA ou CANCELADA, que o funcionário pode trocar a qualquer momento na lista de ordens de serviço.

#### Scenario: Iniciar o serviço
- **WHEN** o funcionário muda a situação de uma OS para EM_ANDAMENTO
- **THEN** a lista passa a mostrar a OS com essa situação

### Requirement: Exclusão da OS
Excluir uma OS SHALL apagar a OS e seus itens e devolver as peças ao estoque.

#### Scenario: Excluir OS com peças
- **WHEN** o funcionário exclui uma OS que usou peças
- **THEN** a OS some da lista e as peças voltam ao estoque
