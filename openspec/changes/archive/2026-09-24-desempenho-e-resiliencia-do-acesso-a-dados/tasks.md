## 1. Cópia em memória

- [x] 1.1 Guardar as listagens por até 5 minutos, com uma trava por tabela; feito em 23/09/2026 (commit `5b1f108`) e verificado na medição registrada no README (telas abrindo em 0,1 a 0,9 s)
- [x] 1.2 Registrar a tarefa de fundo `manter_cache_aquecido` em `harley_store.py`; verificado no código em 07/10/2026 (`app.register_lifespan_task`)
- [x] 1.3 Atualizar a cópia com o registro devolvido a cada gravação, descartando-a em erro; feito em 23/09/2026 (commit `b26972a`) e verificado na produção (venda de 22,9 s para cerca de 1,5 s)

## 2. Novas tentativas e recuperação

- [x] 2.1 Repetir requisições no 429 e em falha de conexão, sem repetir POST; verificado pelo teste automático `test_gravacao_nao_repete_mas_a_proxima_chamada_funciona`
- [x] 2.2 Descartar o cliente HTTP depois de uma falha de conexão; feito em 24/09/2026 (commit `510bf61`) e verificado pelo teste `test_leitura_troca_o_cliente_quebrado_e_funciona`
- [x] 2.3 Aumentar o tempo limite para 30 segundos e registrar no log as falhas de renovação da cópia; verificado no código (`manter_cache_aquecido` registra `cache: nao foi possivel renovar`) e no log da produção de 24/09/2026, onde a falha de conexão ficou registrada (`falha de conexao com o Xano`)

## 3. Mensagens de erro

- [x] 3.1 Criar `erros.py` com as mensagens em português e registrar o tratador no `rx.App`; feito em 24/09/2026 (commit `018aba5`) e verificado no uso real (mensagem "Você não tem permissão..." exibida no incidente da conta de serviço de 01/10/2026)
- [x] 3.2 Rodar os testes automáticos e compilar o app; verificado em 07/10/2026 (44 testes passando e `reflex compile` sem erros)
