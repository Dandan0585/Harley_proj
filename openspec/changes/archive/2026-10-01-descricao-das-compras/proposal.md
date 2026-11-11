## Why

Na tela de Compras não dava para saber o que foi pedido a cada fornecedor sem abrir o documento impresso, e a equipe queria poder escrever a descrição do pedido do seu jeito.

Registro retroativo: implementado em 01/10/2026 (commit `cb9b8ff`); o campo foi aplicado no Xano em 05/10/2026. Esta change documenta o comportamento em uso.

## What Changes

- Nova coluna "Descrição" na lista de compras.
- Ao finalizar uma compra, a descrição é preenchida com os itens (por exemplo, "2x Pneu Traseiro; 10x Óleo 10W30").
- A descrição pode ser reescrita pela equipe; compras antigas mostram a descrição montada pelos itens.

## Capabilities

### New Capabilities
- `compras/descricao-da-compra`: descrição do que foi pedido em cada compra, gerada automaticamente e editável.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Xano**: campo `descricao` (texto, opcional) em `entrada_mercadoria`, gravado pelos endpoints POST e PUT.
- **Código**: `harley_store/state/compras_state.py` e `harley_store/pages/compras.py`.
