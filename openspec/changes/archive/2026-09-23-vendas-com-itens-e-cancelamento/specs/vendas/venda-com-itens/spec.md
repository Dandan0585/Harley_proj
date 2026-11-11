# Spec Delta

## Purpose

Permite registrar uma venda com vários itens (produtos do estoque e itens avulsos), guardando o que foi vendido e baixando o estoque de forma confiável, mesmo com vários funcionários vendendo ao mesmo tempo.

## ADDED Requirements

### Requirement: Venda com vários itens
O sistema SHALL permitir montar uma venda com um ou mais itens antes de registrá-la. Cada item é um produto do estoque (com quantidade e preço unitário, inicialmente o preço de venda do produto) ou um item avulso (descrição, quantidade e valor unitário, sem ligação com o estoque). Os itens MUST poder ser removidos antes do registro. O total da venda MUST ser a soma de quantidade × valor unitário de todos os itens.

#### Scenario: Venda com dois produtos e um item avulso
- **WHEN** o funcionário adiciona 2 unidades de um produto de R$ 42,50, 1 unidade de outro produto de R$ 28,00 e um item avulso "Mão de obra" de R$ 100,00, e registra a venda
- **THEN** uma única venda é registrada com os 3 itens e total de R$ 213,00

#### Scenario: Remover item antes de registrar
- **WHEN** o funcionário adiciona um item por engano e o remove do carrinho
- **THEN** o item não faz parte da venda registrada e o total é recalculado

#### Scenario: Venda sem itens
- **WHEN** o funcionário tenta registrar uma venda sem nenhum item
- **THEN** a venda não é registrada e o sistema informa que é preciso ao menos um item

### Requirement: Itens gravados e consultáveis
Os itens de cada venda registrada MUST ficar gravados, com o produto (ou a descrição do item avulso), a quantidade e o valor unitário. O sistema SHALL exibir os itens de uma venda na consulta da venda e no comprovante impresso.

#### Scenario: Consultar os itens de uma venda
- **WHEN** alguém abre os detalhes ou o comprovante de uma venda registrada por esta versão
- **THEN** são exibidos cada item, sua quantidade, o valor unitário, o subtotal e o total

#### Scenario: Venda antiga sem itens
- **WHEN** alguém consulta uma venda registrada antes desta versão
- **THEN** a venda é exibida com seu valor total e a indicação de que os itens não foram registrados

### Requirement: Baixa de estoque na venda
Ao registrar uma venda, o sistema MUST baixar do estoque a quantidade de cada item que for produto. A venda MUST ser recusada, sem baixar nada, se algum produto não tiver estoque suficiente. Itens avulsos MUST NOT alterar o estoque.

#### Scenario: Estoque suficiente
- **WHEN** uma venda com 2 unidades de um produto com estoque 10 é registrada
- **THEN** o estoque desse produto passa a ser 8

#### Scenario: Estoque insuficiente em um dos itens
- **WHEN** uma venda tem um item com estoque suficiente e outro sem estoque suficiente
- **THEN** a venda não é registrada, nenhum estoque é alterado e o sistema informa qual produto não tem estoque

### Requirement: Estoque correto com vendas simultâneas
Operações de estoque feitas ao mesmo tempo sobre o mesmo produto (vendas, cancelamentos e demais baixas) MUST ser aplicadas uma de cada vez, de forma que nenhuma alteração se perca e o estoque nunca fique negativo.

#### Scenario: Duas vendas simultâneas do mesmo produto
- **WHEN** dois funcionários registram, ao mesmo tempo, uma venda de 1 unidade do mesmo produto com estoque 5
- **THEN** as duas vendas são registradas e o estoque final é 3

#### Scenario: Disputa pela última unidade
- **WHEN** dois funcionários tentam vender, ao mesmo tempo, a última unidade de um produto
- **THEN** apenas uma venda é registrada, a outra é recusada por falta de estoque, e o estoque final é 0

### Requirement: Registro consistente em caso de falha
Se o registro de uma venda falhar no meio (por exemplo, perda de conexão com o banco), o sistema MUST NOT deixar estoque baixado para uma venda que não foi registrada, e MUST informar a falha ao funcionário.

#### Scenario: Falha ao gravar os itens
- **WHEN** a venda é criada, mas a gravação de seus itens falha
- **THEN** o estoque baixado para essa venda é devolvido, a venda não fica ativa e o funcionário é avisado para tentar de novo
