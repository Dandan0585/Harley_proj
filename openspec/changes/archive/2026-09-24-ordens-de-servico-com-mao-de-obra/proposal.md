## Why

A ordem de serviço só registrava peças do estoque. A mão de obra, que é a maior parte do valor de um serviço de oficina, não tinha onde ser lançada, e o valor da OS ficava incompleto.

Registro retroativo: implementado na auditoria de 24/09/2026 (commit `018aba5`). Esta change documenta o comportamento em uso; a data de conclusão e a entrada da OS no faturamento vieram depois, na change `mao-de-obra-no-faturamento`.

## What Changes

- A OS passa a aceitar serviços (descrição e valor), sem mexer no estoque, além das peças.
- O valor sugerido da peça é o preço de venda vezes a quantidade, e pode ser alterado.
- O valor da OS é a soma das peças e dos serviços.

## Capabilities

### New Capabilities
- `oficina/ordens-de-servico`: abertura, itens (peças e serviços), situações e exclusão das ordens de serviço.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/state/os_state.py` e `harley_store/pages/ordens_servico.py`.
- **Xano**: campo `descricao` em `itens_ordem_servico` (nome da peça ou do serviço; serviço com `id_produto = 0`).
