## MODIFIED Requirements

### Requirement: Faturamento separado entre motos e produtos
O faturamento SHALL ser separado em duas categorias, considerando só vendas não canceladas:
- motos: motos marcadas como Vendida, pelo preço de venda, na data de saída, e vendas antigas do tipo MOTO registradas sem itens;
- produtos e serviços: todos os itens de venda, pelo valor do item (quantidade × valor unitário, já com o desconto dado no preço), sejam produtos do estoque ou itens avulsos como mão de obra; as ordens de serviço com a situação CONCLUIDA, pelo valor total da OS (peças e mão de obra), na data de conclusão; e vendas antigas sem itens dos tipos PECAS e BALCAO.

Vendas dos tipos COMPRA e ORDEM_SERVICO MUST ficar de fora; as do tipo ORDEM_SERVICO porque a OS já conta pela própria conclusão. Uma OS concluída sem data de conclusão MUST ficar de fora. Os cards "Faturamento de Motos (mês)" e "Produtos e serviços (mês)" SHALL mostrar o mês corrente, e o card "Faturamento de hoje" o total do dia.

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

### Requirement: Total do dia e do mês junto ao gráfico
O gráfico de faturamento dos últimos 12 meses SHALL somar motos, produtos e serviços, e logo abaixo do título SHALL mostrar o total do dia e o total do mês (motos + produtos e serviços).

#### Scenario: Abrir o Painel
- **WHEN** o dono da loja abre o Painel
- **THEN** vê, junto ao gráfico, "Hoje: R$ …" e "Mês: R$ …" com a soma de motos, produtos e serviços
