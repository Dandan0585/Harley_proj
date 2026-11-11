## Context

Motivação em proposal.md. Esta change reaproveita a trava por produto criada na change `vendas-com-itens-e-cancelamento` (design D2) e resolve o risco que ela deixou registrado ("Compras e OS continuam sem trava"). O Xano Free não tem transações nem chaves estrangeiras entre tabelas. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Um único caminho para alterar saldo de produto.
- Integridade referencial na exclusão, já que o banco não a garante.

**Non-Goals:**
- Atomicidade real no banco (exigiria funções XanoScript com transação).
- Proteção entre processos diferentes (produção e desenvolvimento no mesmo Xano), coberta pela regra de testes do README.

## Decisions

### D1. Um único módulo de estoque
`estoque.movimentar(ajustes)` é usado por vendas, cancelamentos, OS, exclusão de OS, compras e exclusão de compras. `estoque.atualizar_produto(id, dados, variacao)` é usado na edição do produto: sob a mesma trava, relê o produto, aplica a variação e grava o cadastro inteiro (o PATCH do Xano substitui o registro).
- *Alternativa:* o formulário gravar o estoque digitado. Era o comportamento anterior e apagava vendas feitas durante a edição.

### D2. Ordem das operações com compensação
Compras e OS baixam ou somam o estoque primeiro e depois gravam o cabeçalho e os itens; se a gravação falhar, apagam o que foi criado e desfazem a movimentação. A exclusão de compra retira o estoque antes de apagar os registros; se apagar falhar, devolve.

### D3. Histórico em tabela própria, sem bloquear a operação
`registrar_historico()` grava uma linha por produto em `movimentacoes_estoque` depois que a movimentação deu certo; erros ao gravar o histórico só vão para o log.

### D4. Mapa de referências para a exclusão
`dependencias.REFERENCIAS` lista, para cada tabela, quais tabelas apontam para ela e por qual campo. `em_uso()` procura o id nessas tabelas (pela cópia em memória) e devolve os nomes para a mensagem; erros de conexão sobem e a exclusão não acontece.

## Risks / Trade-offs

- [Travas valem só dentro de um processo] → A produção roda com 1 worker de backend (conferido na change de vendas, tarefa 7.1).
- [Tabela nova que aponte para outra] → Precisa ser acrescentada em `REFERENCIAS`, como diz o comentário do módulo.
