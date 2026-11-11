## Why

O dono da loja não conseguia ver no Painel quanto tem parado em estoque nem quanto faturou com motos e com produtos separadamente: o card "Faturamento do mês" somava tudo, inclusive ordens de serviço e até um registro de compra, e o valor do estoque de motos usava o preço de venda.

Registro retroativo: implementado em 01/10/2026 (commit `538cf78`), a partir de um pedido do dono da loja com regras aprovadas antes da implementação. Esta change documenta o comportamento daquela data; a inclusão da mão de obra e das OS veio depois, na change `mao-de-obra-no-faturamento`.

## What Changes

- Novos cards "Estoque de Motos (custo)" e "Estoque de Produtos".
- O card "Faturamento do mês" é substituído por "Faturamento de Motos (mês)" e "Faturamento de Produtos (mês)".
- O gráfico de 12 meses passa a somar só motos e produtos e ganha o total do dia e do mês.
- Dia e mês no fuso de São Paulo; valores calculados sem erro de arredondamento.
- **BREAKING** (valores): o faturamento deixa de contar vendas do tipo COMPRA e ORDEM_SERVICO; o gráfico de fevereiro/2026 passou de R$ 42.121,10 para R$ 19.631,30.

## Capabilities

### New Capabilities
- `painel/visao-financeira`: indicadores financeiros do Painel (valor em estoque e faturamento).

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/state/dashboard_state.py` e `harley_store/pages/dashboard.py`; `requirements.txt` (pacote `tzdata`, fuso de São Paulo no Windows).
- **Xano**: só leitura (inclui a tabela `itens_transacao`).
- **Testes**: novo `tests/test_painel.py`.
