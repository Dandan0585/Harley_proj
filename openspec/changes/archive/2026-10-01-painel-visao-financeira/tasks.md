## 1. Cálculo

- [x] 1.1 Criar as funções de estoque e de faturamento com Decimal e fuso de São Paulo; feito em 01/10/2026 (commit `538cf78`) e verificado pelos testes de `tests/test_painel.py` (moto consignada fora, produto sem estoque fora, venda cancelada, COMPRA e ORDEM_SERVICO fora, vendas antigas, 23:59 e virada do mês, 12 meses, formato e ausência de dados)
- [x] 1.2 Instalar o pacote `tzdata` e registrá-lo em `requirements.txt`; verificado em 01/10/2026 (`America/Sao_Paulo` disponível no Windows)
- [x] 1.3 Ligar as funções ao `DashboardState.carregar`, lendo também `itens_transacao`; verificado no código

## 2. Tela

- [x] 2.1 Trocar "Faturamento do mês" pelos cards de motos e produtos, transformar "Valor do estoque" em "Estoque de Motos (custo)", acrescentar "Estoque de Produtos" e o total do dia e do mês no gráfico, com o mesmo componente de card; verificado no código de `pages/dashboard.py` e com `reflex compile`

## 3. Validação

- [x] 3.1 Comparar o Painel com um cálculo independente sobre os dados reais do Xano; verificado em 01/10/2026: estoque de motos R$ 135.000,00, estoque de produtos R$ 33.263,50, faturamentos do mês R$ 0,00 e fevereiro/2026 R$ 19.631,30, todos iguais nos dois cálculos
