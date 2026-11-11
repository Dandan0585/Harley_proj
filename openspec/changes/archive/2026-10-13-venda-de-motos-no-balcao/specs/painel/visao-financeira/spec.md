## MODIFIED Requirements

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
