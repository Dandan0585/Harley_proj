## 1. Banco de dados (Xano)

- [x] 1.1 Criar `data_conclusao` (timestamp, opcional) em `ordens_servico` e aplicar com `scripts/aplicar_xano.ps1`, depois de conferir na prévia que nenhuma coluna seria apagada; feito em 05/10/2026 e verificado no Xano (o campo é devolvido nas OS)

## 2. Ordens de serviço

- [x] 2.1 Gravar e apagar a data de conclusão em `mudar_status` e mostrar o valor da OS ao concluir; feito em 05/10/2026 (commit `22f5218`) e verificado no uso real: a OS nº 16 foi concluída em 05/10/2026 às 16:15 com a data gravada

## 3. Painel

- [x] 3.1 Incluir os itens avulsos das vendas e as OS concluídas no faturamento e renomear o card para "Produtos e serviços (mês)"; verificado pelos testes `test_venda_soma_produtos_e_mao_de_obra`, `test_balcao_produto_mais_mao_de_obra_no_dia`, `test_os_concluida_soma_pecas_e_mao_de_obra_no_dia_da_conclusao`, `test_os_nao_concluida_cancelada_ou_sem_data_nao_conta` e `test_os_concluida_em_outro_dia_conta_no_mes_mas_nao_hoje`
- [x] 3.2 Validar com os dados reais; verificado em 05/10/2026: faturamento de hoje de R$ 2.138,70 igual nos dois cálculos (venda nº 51 de R$ 1.668,70, com R$ 150,00 de mão de obra, e OS nº 16 de R$ 470,00)
- [x] 3.3 Documentar a regra no README; verificado em 07/10/2026 (descrição do Painel)
