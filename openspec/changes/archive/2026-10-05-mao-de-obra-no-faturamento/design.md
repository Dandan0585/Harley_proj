## Context

Motivação em proposal.md. Nas vendas, o total já somava produtos e mão de obra; só o Painel deixava os itens avulsos de fora (regra da change `painel-visao-financeira`). A OS tinha só a data de abertura, e sem uma data de conclusão não havia como saber em que dia somar o valor. A equipe pediu para não criar campos desnecessários no Xano: este é o único campo novo. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Mão de obra no faturamento sem contar nada em dobro.

**Non-Goals:**
- Card separado para serviços.
- Preencher a data de conclusão das OS concluídas antes desta change.

## Decisions

### D1. Data de conclusão na própria OS
`mudar_status` grava `data_conclusao` quando a OS passa a CONCLUIDA (vinda de outra situação) e grava vazio quando ela sai de CONCLUIDA. O PATCH do endpoint de OS já aceita qualquer campo da tabela, então só a tabela mudou.
- *Alternativa:* criar uma venda do tipo ORDEM_SERVICO ao concluir a OS. Rejeitada: as peças já saíram do estoque na abertura da OS, e o cancelamento dessa venda devolveria as peças em dobro.

### D2. OS no faturamento pela data de conclusão
`lancamentos_faturamento` recebe as OS e os itens de OS e lança, para cada OS CONCLUIDA com data, a soma de `valor_total_item` na categoria "produtos" (exibida como "produtos e serviços").

### D3. Vendas do tipo ORDEM_SERVICO continuam fora
Uma OS lançada também em Vendas com esse tipo contaria em dobro; a regra mantém essas vendas fora e está explicada no topo de `dashboard_state.py`. A orientação de não lançar a OS em Vendas foi passada ao dono da loja em 05/10/2026.

## Risks / Trade-offs

- [OS concluídas antes de 05/10/2026 não contam] → Para contar uma delas, basta mudar para EM_ANDAMENTO e de novo para CONCLUIDA; ela conta na data em que isso for feito.
- [Concluir a OS no dia errado] → O valor entra no dia em que a situação foi trocada; reabrir e concluir de novo corrige a data.
