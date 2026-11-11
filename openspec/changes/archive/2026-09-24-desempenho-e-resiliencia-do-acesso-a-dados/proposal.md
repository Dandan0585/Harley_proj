## Why

O Xano do plano Free leva de 1 a 2 segundos por requisição, limita o número de requisições por minuto (erro 429) e às vezes demora mais de 15 segundos. Com isso as telas demoravam a abrir, vendas esbarravam no limite e uma queda de rede deixava o servidor do app falhando até ser reiniciado. Os erros apareciam em inglês, com detalhes técnicos.

Registro retroativo: implementado em 23/09/2026 (commits `5b1f108` e `b26972a`) e 24/09/2026 (`018aba5` e `510bf61`), sem change no OpenSpec. Esta change documenta o comportamento que está em uso.

## What Changes

- As telas leem as tabelas de uma cópia em memória no servidor, renovada em segundo plano; uma alteração feita fora do app aparece em até 5 minutos.
- Cada gravação feita pelo app atualiza a cópia na hora, sem reler a tabela inteira.
- O limite de requisições (429) e as falhas de rede passam a ser tratados com novas tentativas automáticas, sem repetir criações, para não gravar em dobro.
- O servidor do app se recupera sozinho depois de uma queda de rede e espera até 30 segundos por uma resposta do Xano.
- Erros inesperados aparecem em português, com orientação, e ficam registrados no log.

## Capabilities

### New Capabilities
- `plataforma/acesso-ao-servidor-de-dados`: desempenho e confiabilidade da comunicação entre o app e o servidor de dados (cópia em memória, novas tentativas, recuperação de falhas e mensagens de erro).

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/xano_client.py` (cópia em memória, aquecimento, novas tentativas, cliente HTTP reaproveitado), `harley_store/erros.py` (mensagens e logs) e `harley_store/harley_store.py` (tarefa de fundo e tratador de erros).
- **Xano**: nenhuma mudança de estrutura; menos requisições por tela.
- **Dependências**: nenhuma nova.
