## MODIFIED Requirements

### Requirement: Faturamento separado entre motos e produtos
O faturamento SHALL ser separado em motos e em produtos e serviços, só com vendas não canceladas. Motos: motos marcadas como Vendida, pelo preço de venda, na data de saída, e vendas antigas do tipo MOTO sem itens. Produtos e serviços: os itens de venda (produtos e avulsos, como mão de obra), pelo valor do item com o desconto já no preço; as ordens de serviço concluídas; e vendas antigas sem itens dos tipos PECAS e BALCAO. Registros do tipo COMPRA MUST ficar de fora.

#### Scenario: Venda mista
- **WHEN** uma venda tem dois produtos de R$ 500,00, um produto de R$ 90,00 e um item avulso de R$ 200,00
- **THEN** o faturamento de produtos e serviços soma R$ 1.290,00, incluindo o item avulso

#### Scenario: Venda com produto e mão de obra
- **WHEN** uma venda de balcão tem um produto de R$ 28,00 e mão de obra de R$ 200,00
- **THEN** o faturamento do dia soma R$ 228,00

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

## ADDED Requirements

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
