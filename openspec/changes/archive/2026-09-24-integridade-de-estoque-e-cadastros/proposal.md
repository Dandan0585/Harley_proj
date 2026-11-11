## Why

A change `vendas-com-itens-e-cancelamento` protegeu o estoque só nas vendas e registrou como risco que Compras, Ordens de serviço e a edição de produto continuavam podendo perder movimentações simultâneas. Além disso, o Xano Free não tem chaves estrangeiras: nada impedia apagar um cliente com vendas, deixando o histórico apontando para um registro inexistente. Também não havia como saber por que o saldo de um produto mudou.

Registro retroativo: implementado na auditoria de 24/09/2026 (commit `018aba5`). Esta change documenta o comportamento em uso.

## What Changes

- Todas as movimentações de estoque (vendas, cancelamentos, peças de OS, compras, exclusões de OS e de compras e ajustes na edição do produto) passam pela mesma proteção contra operações simultâneas, nunca deixam saldo negativo e desfazem o que já foi feito em caso de falha.
- A edição do produto passa a aplicar a variação digitada sobre o saldo atual, sem apagar vendas feitas enquanto o formulário estava aberto.
- Excluir uma compra retira do estoque o que ela somou e é recusado se parte já foi vendida; excluir uma OS devolve as peças.
- Novo histórico de movimentações por produto, com origem, documento, quantidade, saldo e usuário.
- Exclusão de cliente, fornecedor, funcionário, moto de cliente e produto é recusada quando há registros ligados.

## Capabilities

### New Capabilities
- `estoque/movimentacao-de-estoque`: regras de alteração do saldo dos produtos e o histórico de movimentações.
- `cadastros/exclusao-protegida`: recusa da exclusão de cadastros que estão em uso.

### Modified Capabilities
<!-- Nenhuma: a capacidade vendas/venda-com-itens continua valendo como está; esta change estende a mesma proteção às demais operações. -->

## Impact

- **Código**: `harley_store/estoque.py` (`movimentar`, `atualizar_produto`, `registrar_historico`), `harley_store/dependencias.py`, `state/compras_state.py`, `state/os_state.py`, `state/produtos_state.py` e as telas de cadastro.
- **Xano**: nova tabela `movimentacoes_estoque` com endpoints de listar e criar.
- **Usuários**: exclusões antes permitidas passam a ser recusadas com explicação.
