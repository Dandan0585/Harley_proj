## 1. Banco de dados (Xano)

- [x] 1.1 Criar o campo `descricao` em `itens_ordem_servico`; feito em 24/09/2026 e verificado no espelho `xano/table/itens_ordem_servico.xs` e nos 12 itens de OS reais em 07/10/2026

## 2. Tela

- [x] 2.1 Adicionar a linha de serviço (descrição e valor) e a sugestão de valor da peça; feito em 24/09/2026 (commit `018aba5`) e verificado no código de `os_state.py` (`adicionar_servico` e `_sugerir_valor`)
- [x] 2.2 Gravar serviços sem movimentar o estoque e mostrar o valor total na lista; verificado no uso real de 05/10/2026: a OS nº 16 foi aberta com a bateria (R$ 220,00) e a mão de obra (R$ 250,00), e o histórico de estoque registra a baixa só da bateria
- [x] 2.3 Compilar o app; verificado em 07/10/2026 (`reflex compile` sem erros)
