# Design

## Context

Motivação em proposal.md; requisitos em `specs/vendas/venda-com-itens/spec.md` e `specs/vendas/cancelamento-de-vendas/spec.md`.

Estado atual verificado:
- `transacoes` (Xano) tem só `tipo_transacao`, `id_funcionario`, `id_cliente`, `id_moto_cliente`, `data_transacao` e `valor_total`. Vazios são `0`, por causa da importação CSV. Não existe tabela de itens (`GET /itens_transacao` → 404).
- `VendasState.salvar` baixa o estoque de **um** produto lendo o registro e fazendo PATCH do registro inteiro. `excluir` apaga a transação sem devolver estoque.
- O PATCH do Xano substitui o registro inteiro: campo omitido volta vazio.
- O plano Free do Xano não permite criar tabelas ou campos pela API, então as mudanças de schema são manuais, no painel.
- `xano_client` mantém cache de listagens (5 min, limpo a cada gravação) e aquece as tabelas em segundo plano. `buscar()` lê do cache.
- A produção roda **um único processo de backend**: sem Redis, o Reflex 0.7.14 usa 1 worker do granian (`processes.get_num_workers`). O desenvolvimento roda outro processo, apontando para o mesmo Xano.
- Consumidores de `transacoes`: Vendas (lista e registro), Painel (faturamento, gráfico, atividade recente) e comprovante impresso.

## Goals / Non-Goals

**Goals:**
- Nenhuma alteração de estoque perdida entre operações simultâneas no processo de produção.
- Falhas no meio de um registro ou cancelamento nunca deixam estoque baixado sem venda ativa, nem devolvido em dobro.
- Compatibilidade total com as vendas existentes (sem itens, sem `status`).

**Non-Goals:**
- Atomicidade real no banco. Exigiria mover a lógica para funções XanoScript, o que fica para uma change própria.
- Proteção entre processos diferentes (produção × desenvolvimento no mesmo Xano). Coberta pela regra de testes já registrada no README.
- Edição de vendas registradas.

## Decisions

### D1. Schema no Xano (manual, pelo usuário)
- Nova tabela `itens_transacao`: `id`, `transacao_id` (int), `produto_id` (int, **0 = item avulso**), `descricao` (text), `quantidade` (int), `valor_unitario` (decimal), com os 5 endpoints de CRUD no **mesmo grupo de API** das demais tabelas (`api:LtU_pM2N`), criados pelo assistente "CRUD Database Operations" do Xano.
- Em `transacoes`: `status` (text; `ATIVA` ou `CANCELADA`; vazio = ativa), `data_cancelamento` (timestamp, opcional) e `motivo_cancelamento` (text, opcional).
- **Ajuste feito no Apply:** o usuário criou os campos como `transacao_id` e `produto_id`, seguindo a convenção do `xano/knowledge/agents.md` (sufixo `_id`), e não `id_transacao`/`id_produto` como este design previa. O código se adaptou ao banco real, com os nomes centralizados em `CAMPO_VENDA`/`CAMPO_PRODUTO` em `vendas_servico.py`. Como o Xano **ignora em silêncio** campos com nome diferente do schema (grava 0), o registro confere, após gravar cada item, que ele ficou ligado à venda; se não ficou, trata como falha e desfaz (D3).
- `valor_total` continua gravado na transação (soma dos itens), para a lista e o faturamento não precisarem ler os itens.
- `descricao` é gravada também para produtos, como uma cópia do nome no momento da venda: o comprovante continua correto mesmo se o produto for renomeado ou excluído.
- *Alternativa:* guardar os itens como JSON num campo texto da transação. Rejeitada: foge do padrão das outras tabelas de itens e dificulta relatórios.

### D2. Trava por produto no servidor (`harley_store/estoque.py`)
Módulo novo com `async def movimentar(ajustes: dict[int, int])`, onde `ajustes` mapeia produto para variação (negativa na venda, positiva no cancelamento). Ele:
1. adquire uma `asyncio.Lock` por produto, **em ordem crescente de id**, para evitar deadlock entre operações com os mesmos produtos em ordens diferentes;
2. relê cada produto **direto do Xano**, sem cache;
3. valida que nenhum estoque ficaria negativo; se ficar, não altera nada e levanta erro com o nome do produto;
4. aplica os PATCHs, com o registro completo;
5. se um PATCH falhar, desfaz os já aplicados.

Todas as baixas e devoluções de estoque de vendas passam por ele. Compras e OS continuam como estão (fora do escopo), e isso é registrado como risco.
- *Alternativa:* função no Xano com transação. É o ideal, mas exige escrever e publicar XanoScript pelo painel, e fica para depois.
- *Alternativa:* trava global única. É mais simples, mas serializa vendas de produtos diferentes sem necessidade.

### D3. Ordem do registro da venda (com compensação)
1. `estoque.movimentar({produto: -qtd, ...})` valida e baixa tudo, ou nada.
2. Cria a transação com `status = ATIVA` e o total.
3. Cria os itens.

Se a etapa 2 falhar, o estoque é devolvido. Se a etapa 3 falhar, o estoque é devolvido e a transação é marcada `CANCELADA` com motivo "Falha ao registrar os itens". Em ambos os casos o funcionário é avisado. Baixar primeiro garante que duas vendas da última unidade não sejam ambas registradas.

### D4. Cancelamento: marcar primeiro, devolver depois
Com uma trava por venda (`asyncio.Lock` por id da transação):
1. relê a transação direto do Xano; se já estiver `CANCELADA`, não faz nada;
2. PATCH da transação completa com `status = CANCELADA`, `data_cancelamento` e `motivo_cancelamento`;
3. lê os itens da venda e chama `estoque.movimentar({produto: +qtd})` para os itens com produto.

Marcar antes de devolver garante que uma nova tentativa nunca devolva o estoque em dobro. O custo aceito: se a etapa 3 falhar, a venda fica cancelada com o estoque não devolvido, e o sistema avisa exatamente quais produtos conferir.
- *Alternativa:* devolver antes de marcar. Rejeitada, porque uma nova tentativa depois de falha devolveria em dobro.

### D5. Cancelamento em lote
As vendas selecionadas são canceladas **uma a uma, em sequência** (D4 para cada uma), para não estourar o limite de requisições do Xano Free. Ao final aparece um resumo com o número de canceladas e as que falharam, com o motivo. O spinner global de loading cobre a espera.

### D6. Tela de Vendas
- **Formulário**: cabeçalho (tipo, funcionário, cliente, moto), o "carrinho" e o total calculado (somente leitura). O carrinho tem uma linha para adicionar produto (produto, quantidade, preço unitário já preenchido e editável, para descontos) e outra para item avulso (descrição, quantidade, valor), com uma tabela de itens com remover. "Registrar venda" fica desabilitado com o carrinho vazio.
- **Lista**: coluna de seleção (só nas ativas), situação ("Ativa" ou "Cancelada", com ícone e texto, e a data do cancelamento), número de itens, "Imprimir" e "Cancelar" (só nas ativas). Barra "Cancelar selecionadas (n)". Os dois diálogos de cancelamento pedem o motivo opcional. Linhas canceladas aparecem esmaecidas. O botão "Excluir" sai.
- A **consulta dos itens** de uma venda é o comprovante (botão Imprimir), que já abre em nova aba. Não se cria outra tela de detalhes.

### D7. Faturamento e comprovante
- Painel: transações com `status == CANCELADA` saem do faturamento de hoje, do mês e do gráfico. Na atividade recente aparecem como "Venda (cancelada)".
- Comprovante: lista os itens de `itens_transacao` (vendas antigas mostram "Itens não registrados (venda anterior a esta versão)" e o total). Uma venda cancelada ganha uma faixa destacada "VENDA CANCELADA", com data e motivo.

### D8. Cache
`itens_transacao` entra em `TABELAS_AQUECIDAS`. As leituras dentro de `estoque.movimentar` e da trava de cancelamento vão direto ao Xano, e todas as gravações limpam o cache da tabela, como já acontece hoje.

**Ajuste feito no Apply (desempenho):** medido na produção, uma venda levou 22,9 s porque cada gravação descartava o cache e a tela relia produtos, vendas e itens. Isso somava requisições, e o Xano Free respondeu 429 ("espere 20 s"). As gravações passaram a **atualizar o cache com o registro devolvido pelo Xano** (`xano_client._aplicar_no_cache`), sem reler a tabela; em caso de erro, o cache da tabela é descartado. Os itens de uma venda são lidos do cache, porque nunca mudam depois de criados. Se uma venda nova não tiver itens no cache, pode ter sido criada por outro processo, e o serviço confere direto no Xano. As releituras diretas de segurança (produto dentro da trava de estoque e venda dentro da trava de cancelamento) foram mantidas. Resultado: registrar faz 4 requisições (antes, ~7 com recarga da tela) em ~1,5 s.

## Risks / Trade-offs

- **[Mais de um processo de backend]** → As travas em memória só valem dentro de um processo. Hoje a produção tem 1 worker, por não ter Redis. Se um dia houver Redis ou mais workers, a proteção precisa migrar para o Xano. Mitigação: comentário no módulo `estoque.py` e verificação na tarefa 7.x.
- **[Dev e produção no mesmo Xano]** → Operações simultâneas vindas dos dois ambientes não são serializadas. Mitigação: a regra de testes do README (só registros de teste, sem testes de estoque em produtos reais).
- **[Compras e OS continuam sem trava]** → Uma entrada de mercadoria simultânea a uma venda do mesmo produto ainda pode perder uma alteração. É raro. Mitigação: estender `estoque.movimentar` para Compras e OS numa próxima change.
- **[Falha na devolução após marcar cancelada]** → A venda fica cancelada sem devolução; o aviso lista os produtos para ajuste manual (D4).
- **[Dependência de ação manual no Xano]** → Sem a tabela e os campos, o app não funciona. Mitigação: as tarefas 1.x são as primeiras e verificáveis, e o código só é publicado depois delas.
- **[Mais requisições por venda]** → Registrar faz 1 leitura e 1 PATCH por produto, 1 POST da venda e 1 POST por item. Uma venda de 3 produtos faz cerca de 10 requisições, perto do limite do Xano Free. Mitigação: os retries com espera já existentes, e o spinner mostra que a operação está em andamento.

## Migration Plan

1. Usuário cria a tabela, os endpoints e os campos no Xano (tarefas 1.x); o app verifica com leitura e gravação de teste, removidas em seguida.
2. Código implementado e testado no desenvolvimento, com produtos e vendas de teste criados e removidos.
3. Publicação na produção com `scripts/publicar.ps1`.
4. As vendas existentes continuam funcionando (status vazio = ativa, sem itens).

**Rollback:** `atualizar_producao.ps1 -Tag <tag anterior>`. A tabela e os campos novos no Xano podem permanecer, porque a versão anterior os ignora.

## Open Questions

- Nenhuma que mude requisitos ou tarefas. Os valores padrão dos motivos de cancelamento (lista de opções × texto livre) seguem como texto livre opcional e podem ser refinados depois.
