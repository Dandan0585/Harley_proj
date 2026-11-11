## Context

Motivação em proposal.md. Todo acesso a dados passa por `harley_store/xano_client.py`, com funções simples (`listar`, `buscar`, `criar`, `atualizar`, `excluir`). As tabelas da loja são pequenas (dezenas de registros), então guardá-las inteiras em memória é barato. Registro retroativo: o código já existia quando este desenho foi escrito, em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Abrir telas sem esperar o Xano e sem estourar o limite de requisições do plano Free.
- Nunca gravar em dobro por causa de uma nova tentativa.

**Non-Goals:**
- Cache compartilhado entre processos (produção e desenvolvimento têm cópias separadas).
- Paginação no servidor (as tabelas ainda são pequenas).

## Decisions

### D1. Cópia em memória com validade de 5 minutos
`listar()` devolve uma cópia da tabela guardada por até 5 minutos, com uma trava por tabela para que várias telas pedindo a mesma tabela façam uma só chamada. `buscar()` procura o registro nessa cópia. `buscar_direto()` lê sem cópia e é usado antes de regravar um registro inteiro (o PATCH do Xano substitui o registro).

### D2. Aquecimento em segundo plano
`manter_cache_aquecido()` é registrada como tarefa de fundo do app. Na subida, renova uma tabela a cada 3 segundos; depois, uma a cada 20 segundos, de modo que cada tabela é renovada antes de vencer a validade. É 1 requisição a cada 20 segundos, bem abaixo do limite do plano Free.

### D3. Gravação atualiza a cópia ("write-through")
O Xano devolve o registro completo depois de criar ou alterar; esse registro é aplicado na cópia em memória. Em qualquer erro, a cópia da tabela é descartada. Medido na produção em 23/09/2026: registrar uma venda caiu de 22,9 s para cerca de 1,5 s (design da change `vendas-com-itens-e-cancelamento`, D8).
- *Alternativa:* descartar a cópia a cada gravação. Era o comportamento anterior e somava releituras até o Xano responder 429.

### D4. Novas tentativas
`_request()` repete até 5 vezes: na resposta 429, com espera crescente ou o tempo do cabeçalho `Retry-After` (até 20 s); em falha de conexão, só para GET, PATCH, PUT e DELETE. POST nunca é repetido após falha de conexão. O cliente HTTP é reaproveitado (keep-alive) e descartado depois de uma falha de conexão, porque o pool podia ficar inutilizável mesmo com a rede de volta. O tempo limite é de 30 segundos.

### D5. Tratador de erros do app
`erros.tratar_erro_backend` é registrado como `backend_exception_handler` do Reflex: grava o erro completo no log e mostra ao funcionário a mensagem de `mensagem_amigavel()`, conforme o tipo de erro.

## Risks / Trade-offs

- [Alteração feita fora do app demora até 5 minutos para aparecer] → Aceito e informado no README (seção Desempenho).
- [Produção e desenvolvimento têm cópias separadas] → Uma gravação feita em um aparece no outro em até 5 minutos; as operações de estoque releem o produto direto do Xano (change `integridade-de-estoque-e-cadastros`).
- [Memória] → As tabelas são pequenas; se crescerem muito, rever a estratégia.
