## Context

Motivação em proposal.md. A tabela `itens_ordem_servico` já tinha `id_os`, `id_produto`, `quantidade` e `valor_total_item`. As movimentações de estoque da OS seguem a change `integridade-de-estoque-e-cadastros`. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Lançar a mão de obra sem criar uma tabela nova.

**Non-Goals:**
- Tabela de preços de serviços.
- Faturamento da OS (change `mao-de-obra-no-faturamento`).

## Decisions

### D1. Serviço como item com `id_produto = 0`
O serviço é gravado em `itens_ordem_servico` com `id_produto = 0`, quantidade 1, o valor e a descrição no campo novo `descricao`. Peças também gravam a descrição (o nome no momento do lançamento), para o documento impresso continuar correto se o produto for renomeado.
- *Alternativa:* tabela própria de serviços. Rejeitada: mais endpoints e consultas para o mesmo resultado.

### D2. Valor total por item
Cada item guarda o valor total (`valor_total_item`), não o unitário, como já era o esquema da tabela; o valor sugerido da peça é preço × quantidade.

## Risks / Trade-offs

- [Item com `id_produto = 0` em telas antigas] → As telas e o documento impresso usam a descrição gravada; peças sem descrição mostram o nome do produto.
