# Tasks

Legenda: **[você]** = feito pelo usuário no painel do Xano (o plano Free não permite criar tabelas ou campos pela API).
Regra de testes: o desenvolvimento usa o mesmo Xano da produção. Todo teste usa produtos, clientes e vendas criados só para o teste (nome com "TESTE"), removidos ao final.

## 1. Banco de dados (Xano)

- [x] 1.1 [você] Criar a tabela `itens_transacao` com os campos `transacao_id` (int), `produto_id` (int), `descricao` (text), `quantidade` (int) e `valor_unitario` (decimal), e gerar os endpoints de CRUD dela no mesmo grupo de API das outras tabelas; verificar com `GET .../api:LtU_pM2N/itens_transacao` respondendo 200
- [x] 1.2 [você] Adicionar à tabela `transacoes` os campos `status` (text), `data_cancelamento` (timestamp, opcional) e `motivo_cancelamento` (text, opcional); verificar que os endpoints POST e PATCH de `transacoes` aceitam os campos novos (se o endpoint foi gerado antes, atualizar os inputs dele no Xano)
- [x] 1.3 Verificar pelo app com uma venda de teste: criar uma transação TESTE com `status`, criar um item para ela, fazer o PATCH completo com `status = CANCELADA`, conferir que os três campos novos foram gravados e que os demais não foram zerados, e apagar os registros de teste
- [x] 1.4 Atualizar o espelho local: `xano/table/transacoes.xs` (campos novos) e o novo `xano/table/itens_transacao.xs` (com comentário de propósito no topo); verificar que os campos batem com um registro real lido do Xano

## 2. Estoque protegido contra concorrência

- [x] 2.1 Criar `harley_store/estoque.py` com `movimentar(ajustes)`: travas por produto em ordem crescente de id, releitura direta do Xano, validação de estoque não negativo antes de qualquer gravação, PATCH do registro completo e desfazer em caso de falha parcial; documentar no módulo o pressuposto de processo único (design D2)
- [x] 2.2 Testar `movimentar` com 2 produtos TESTE: baixa válida, recusa sem alteração quando um dos produtos não tem estoque, e 10 baixas simultâneas de 1 unidade (`asyncio.gather`) resultando exatamente em estoque − 10; na disputa pela última unidade, só uma baixa passa

## 3. Registro de venda com itens

- [x] 3.1 Em `vendas_state.py`, criar o carrinho: adicionar produto (quantidade e preço unitário preenchido e editável), adicionar item avulso (descrição, quantidade, valor), remover item e total calculado; verificar que o total é a soma de quantidade × valor unitário
- [x] 3.2 Reescrever `salvar` na ordem do design D3 (baixar estoque → criar transação ATIVA → criar itens), com a compensação em cada falha; verificar com uma venda TESTE de 2 produtos + 1 avulso que a venda, os 3 itens e as baixas foram gravados
- [x] 3.3 Verificar a compensação simulando falha na criação dos itens: o estoque volta ao valor anterior, a transação fica CANCELADA com o motivo de falha e o aviso aparece
- [x] 3.4 Atualizar o formulário em `pages/vendas.py` (carrinho, item avulso, total somente leitura, "Registrar venda" desabilitado com o carrinho vazio); verificar no navegador o registro de uma venda TESTE

## 4. Cancelamento

- [x] 4.1 Implementar o cancelamento de uma venda conforme o design D4 (trava por venda, releitura, marcar CANCELADA com data e motivo, devolver estoque dos itens com produto, aviso para venda antiga sem itens); verificar com a venda TESTE da 3.2 que o estoque voltou e a venda continua listada como cancelada
- [x] 4.2 Verificar o cancelamento único: duas chamadas simultâneas de cancelamento da mesma venda TESTE devolvem o estoque uma única vez
- [x] 4.3 Implementar o cancelamento em lote (sequencial, resumo com canceladas e falhas); verificar com 3 vendas TESTE
- [x] 4.4 Atualizar a lista em `pages/vendas.py`: seleção só nas ativas, situação com ícone e texto, data de cancelamento, número de itens, "Cancelar" com motivo (individual e "Cancelar selecionadas (n)"), linhas canceladas esmaecidas e remoção do "Excluir"; verificar no navegador

## 5. Faturamento e comprovante

- [x] 5.1 Em `dashboard_state.py`, tirar as vendas canceladas do faturamento de hoje, do mês e do gráfico, e identificá-las na atividade recente; verificar que cancelar uma venda TESTE de hoje reduz o faturamento de hoje exatamente pelo valor dela
- [x] 5.2 Em `impressao_state.py` e `pages/impressao.py`: itens gravados, aviso para venda antiga sem itens e faixa "VENDA CANCELADA" com data e motivo; verificar imprimindo uma venda TESTE ativa, a mesma cancelada e a venda antiga nº 1
- [x] 5.3 Incluir `itens_transacao` em `TABELAS_AQUECIDAS` (`xano_client.py`); verificar que a tela de Vendas continua abrindo em menos de 1 s com o cache quente

## 6. Limpeza e documentação

- [x] 6.1 Remover todos os registros TESTE criados (vendas, itens e produtos) e conferir no Xano, sem cache, que nada restou e que o estoque dos produtos reais não mudou em relação ao início dos testes (conferido em 07/10/2026: a busca por "teste" em 11 tabelas do Xano — produtos, clientes, vendas, itens de venda, fornecedores, funcionários, motos da loja, motos de clientes, OS, itens de OS e compras — não encontrou nenhum registro. O saldo dos produtos reais no início dos testes de 23/09 não pôde ser reconferido depois do fato.)
- [x] 6.2 Atualizar o README: remover a seção "Limitação herdada" (vendas sem itens) e documentar vendas com vários itens, cancelamento com devolução de estoque e cancelamento em lote (conferido em 07/10/2026: a seção "Limitação herdada" não existe mais; "O que o app faz" descreve a venda com vários itens e o cancelamento de uma ou várias vendas com devolução do estoque, e a seção "Vendas antigas (antes do registro de itens)" explica as vendas importadas.)

## 7. Publicação

- [x] 7.1 Confirmar que a produção roda com 1 worker de backend (pressuposto do design D2), pela linha de comando do granian no log de produção; publicar com `scripts/publicar.ps1` e verificar em `http://192.168.0.54:3000` o registro e o cancelamento de uma venda TESTE, removida em seguida (conferido em 07/10/2026, com um desvio. 1 worker: o log da produção não mostra a linha do granian, então a conferência foi pelo código do Reflex 0.7.14, que só usa mais de um worker com Redis ou `gunicorn_workers`, e nenhum dos dois está configurado em `rxconfig.py`, nos scripts ou em `producao.local.ps1`. Publicação: tags `prod-20260923-1558` e `prod-20260923-1615`, com uso real medido na produção (design D8). Registro e cancelamento: conferidos no uso real de 05/10/2026, no desenvolvimento e no mesmo Xano — a venda nº 50 foi registrada e cancelada, e o histórico de estoque mostra a baixa às 13:08 e a devolução às 15:58. Desvio: a conferência não foi refeita no endereço da produção, que está pausada desde 25/09/2026 (modo demonstração).)
