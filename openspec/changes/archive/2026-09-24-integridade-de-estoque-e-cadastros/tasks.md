## 1. Estoque

- [x] 1.1 Passar compras, exclusão de compras, OS e exclusão de OS por `estoque.movimentar`, com compensação em falha; feito em 24/09/2026 (commit `018aba5`) e verificado pelos testes `test_tudo_ou_nada`, `test_falha_no_meio_desfaz` e `test_baixas_simultaneas_nao_se_perdem`
- [x] 1.2 Criar `estoque.atualizar_produto` para a edição do produto; verificado pelos testes `test_edicao_do_cadastro_nao_apaga_venda_simultanea` e `test_edicao_recusa_saldo_negativo`
- [x] 1.3 Recusar a exclusão de compra cujos produtos já saíram do estoque; verificado no código de `compras_state.py` (mensagem "parte dos produtos já saiu do estoque")

## 2. Histórico

- [x] 2.1 Criar a tabela `movimentacoes_estoque` no Xano e `estoque.registrar_historico`; verificado pelo teste `test_historico_grava_e_nunca_quebra_a_operacao` e, em 07/10/2026, pelos 27 registros reais da tabela (incluindo a venda e o cancelamento da venda nº 50 em 05/10/2026)
- [x] 2.2 Mostrar o histórico do produto na tela Produtos (botão "Histórico", 100 mais recentes); verificado no código de `produtos_state.py` e `pages/produtos.py`

## 3. Exclusão protegida

- [x] 3.1 Criar `dependencias.py` com o mapa de referências e usá-lo nas exclusões de clientes, fornecedores, funcionários, motos de clientes e produtos; verificado em 07/10/2026 (`em_uso` chamado nos cinco states)
- [x] 3.2 Rodar os testes automáticos; verificado em 07/10/2026 (44 testes passando)
