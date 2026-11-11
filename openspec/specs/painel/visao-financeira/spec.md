# painel/visao-financeira Specification

## Purpose
Mostra ao dono da loja, no Painel, quanto há em estoque e quanto foi faturado, separando motos de produtos, com valores calculados a partir dos dados reais do banco.

## Requirements

### Requirement: Estoque de motos pelo preço de compra
O card "Estoque de Motos (custo)" SHALL mostrar a soma do preço de compra das motos da loja nas situações Em estoque, Em preparação, Em manutenção, Reservada e Indisponível. Motos Vendidas e Consignadas MUST ficar de fora, e uma moto sem preço de compra conta como R$ 0,00.

#### Scenario: Moto consignada
- **WHEN** a loja tem uma moto Em estoque com preço de compra de R$ 100.000,00 e uma moto Consignada de R$ 80.000,00
- **THEN** o card mostra R$ 100.000,00

### Requirement: Estoque de produtos pelo preço de venda
O card "Estoque de Produtos" SHALL mostrar a soma de quantidade × preço de venda dos produtos com estoque maior que zero.

#### Scenario: Produto sem estoque
- **WHEN** um produto tem estoque 0
- **THEN** ele não entra na soma

### Requirement: Faturamento separado entre motos e produtos
O faturamento SHALL ser separado em motos e em produtos e serviços, só com vendas não canceladas. Motos: motos Vendidas, inclusive no Balcão, pelo preço de venda, na data de saída, e vendas antigas do tipo MOTO sem itens. Produtos e serviços: itens de venda (produtos e avulsos, como mão de obra), pelo valor do item; OS concluídas; e vendas antigas sem itens dos tipos PECAS e BALCAO. O item que é moto da loja MUST NOT entrar em produtos e serviços. Registros do tipo COMPRA MUST ficar de fora.

#### Scenario: Venda mista
- **WHEN** uma venda tem dois produtos de R$ 500,00, um produto de R$ 90,00 e um item avulso de R$ 200,00
- **THEN** o faturamento de produtos e serviços soma R$ 1.290,00, incluindo o item avulso

#### Scenario: Venda com produto e mão de obra
- **WHEN** uma venda de balcão tem um produto de R$ 28,00 e mão de obra de R$ 200,00
- **THEN** o faturamento do dia soma R$ 228,00

#### Scenario: Moto vendida no Balcão
- **WHEN** hoje é registrada no Balcão a venda de uma moto de R$ 120.000,00 com um capacete de R$ 1.500,00
- **THEN** o faturamento de motos aumenta R$ 120.000,00, o de produtos e serviços aumenta R$ 1.500,00 e o de hoje aumenta R$ 121.500,00

#### Scenario: OS concluída hoje
- **WHEN** uma OS com uma peça de R$ 220,00 e mão de obra de R$ 250,00 é marcada como CONCLUIDA hoje
- **THEN** o faturamento de hoje e o de produtos e serviços do mês aumentam R$ 470,00

#### Scenario: OS não concluída
- **WHEN** uma OS está ABERTA, EM_ANDAMENTO ou CANCELADA
- **THEN** o valor dela não entra no faturamento

#### Scenario: Venda cancelada
- **WHEN** uma venda do mês é cancelada
- **THEN** ela sai do faturamento de hoje, do mês e do gráfico

#### Scenario: Registro do tipo COMPRA
- **WHEN** existe um registro de venda do tipo COMPRA
- **THEN** ele não entra no faturamento

### Requirement: Período no fuso de São Paulo
O dia e o mês SHALL ser contados no fuso de São Paulo: o dia vai das 00:00 às 23:59, e o mês do dia 1, às 00:00, até o fim do dia atual.

#### Scenario: Venda às 23:59
- **WHEN** uma venda é registrada às 23:59 de 14/10 no horário de São Paulo, que já é 15/10 em UTC
- **THEN** ela conta no faturamento de 14/10

#### Scenario: Virada do mês
- **WHEN** uma venda é registrada às 23:00 de 30/09 no horário de São Paulo
- **THEN** ela conta em setembro, e não em outubro

### Requirement: Total do dia e do mês junto ao gráfico
O gráfico de faturamento dos últimos 12 meses SHALL somar motos, produtos e serviços, e logo abaixo do título SHALL mostrar o total do dia e o total do mês (motos + produtos e serviços).

#### Scenario: Abrir o Painel
- **WHEN** o dono da loja abre o Painel
- **THEN** vê, junto ao gráfico, "Hoje: R$ …" e "Mês: R$ …" com a soma de motos, produtos e serviços

### Requirement: Valores exatos e sem zero falso
Os valores SHALL ser calculados sem erro de arredondamento de centavos e exibidos no formato R$ 1.234,56. Sem dados no período, o card MUST mostrar R$ 0,00; se a leitura dos dados falhar, os cards financeiros MUST mostrar "—", e não um zero que pareça verdadeiro.

#### Scenario: Três unidades de R$ 0,10
- **WHEN** um produto tem 3 unidades de R$ 0,10 em estoque
- **THEN** o estoque de produtos soma exatamente R$ 0,30

### Requirement: Ordens de serviço no faturamento
Uma ordem de serviço com a situação CONCLUIDA SHALL contar em produtos e serviços pelo valor total da OS (peças e mão de obra), na data de conclusão. Uma OS concluída sem data de conclusão MUST ficar de fora. Vendas do tipo ORDEM_SERVICO MUST ficar de fora, porque a OS já conta pela própria conclusão.

#### Scenario: OS concluída antes de existir a data de conclusão
- **WHEN** uma OS está CONCLUIDA, mas não tem data de conclusão
- **THEN** o valor dela não entra no faturamento

#### Scenario: Venda antiga do tipo ORDEM_SERVICO
- **WHEN** existe uma venda antiga do tipo ORDEM_SERVICO
- **THEN** ela não entra no faturamento, para a OS não contar em dobro

### Requirement: Cards de faturamento
Os cards "Faturamento de Motos (mês)" e "Produtos e serviços (mês)" SHALL mostrar o mês corrente, e o card "Faturamento de hoje" SHALL mostrar o total do dia (motos mais produtos e serviços).

#### Scenario: Card de hoje
- **WHEN** hoje houve uma venda de R$ 228,00 e uma moto vendida de R$ 100.000,00
- **THEN** o card "Faturamento de hoje" mostra R$ 100.228,00
