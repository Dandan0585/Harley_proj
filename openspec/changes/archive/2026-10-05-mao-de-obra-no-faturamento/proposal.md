## Why

O valor de mão de obra lançado nas vendas de balcão e nas ordens de serviço não entrava no faturamento do Painel, porque a regra de 01/10/2026 deixava de fora os itens avulsos e as OS. O dono da loja pediu que a mão de obra fosse somada junto aos produtos: nas vendas, quando são registradas, e nas OS, quando são concluídas.

Registro retroativo: implementado em 05/10/2026 (commit `22f5218`), com o campo novo aplicado no Xano no mesmo dia. Esta change documenta o comportamento em uso.

## What Changes

- Os itens avulsos das vendas (mão de obra) passam a contar no faturamento, junto com os produtos.
- Ao marcar uma OS como CONCLUIDA, o sistema grava a data de conclusão, e o valor da OS (peças e mão de obra) entra no faturamento desse dia; se a OS sair de CONCLUIDA, o valor sai do faturamento.
- O card "Faturamento de Produtos (mês)" passa a se chamar "Produtos e serviços (mês)", e o gráfico e os totais do dia e do mês passam a incluir os serviços.
- Vendas do tipo ORDEM_SERVICO continuam fora, para a OS não contar em dobro.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `painel/visao-financeira`: o faturamento passa a incluir a mão de obra das vendas e as OS concluídas, e os rótulos mudam para "produtos e serviços".
- `oficina/ordens-de-servico`: a OS passa a registrar a data de conclusão.

## Impact

- **Xano**: campo `data_conclusao` (timestamp, opcional) em `ordens_servico`; o endpoint PATCH já grava qualquer campo da tabela.
- **Código**: `harley_store/state/os_state.py`, `harley_store/state/dashboard_state.py` e `harley_store/pages/dashboard.py`.
- **Dados**: OS concluídas antes desta change não têm data de conclusão e não entram no faturamento.
