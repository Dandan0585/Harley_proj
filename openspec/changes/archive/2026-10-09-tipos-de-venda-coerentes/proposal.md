## Why

A tela de Vendas oferece os tipos `COMPRA` e `ORDEM_SERVICO`, que não são vendas: compras têm a tela Compras e a OS entra no faturamento quando é concluída. Por isso, a compra de uma moto usada da cliente Helena (R$ 22.000, 15/02/2026) ficou registrada como "venda nº 8" do tipo COMPRA, e o mesmo erro pode se repetir. O Explore de 09/10/2026 também encontrou o preço de compra da moto da loja nº 15 gravado como R$ 119,95, o que deixa o Estoque de Motos do Painel quase R$ 120 mil abaixo do real.

## What Changes

- A tela de Vendas passa a oferecer só os tipos **BALCAO**, **PECAS** e **MOTO**. O servidor recusa qualquer outro tipo, mesmo enviado direto pelo websocket.
- O tipo **MOTO** na tela de Vendas significa peças e serviços para a moto do cliente e conta no faturamento de **Produtos** (regra atual do Painel, mantida). A moto da loja continua sendo vendida em Produtos > Motos.
- As vendas antigas dos tipos `COMPRA` e `ORDEM_SERVICO` continuam no histórico, com a mesma regra de faturamento de hoje (fora do faturamento).
- Correções de dados no Xano, aprovadas pelo grupo no Explore de 09/10/2026:
  - a venda nº 8 (COMPRA, R$ 22.000) é **cancelada** com o motivo "Compra da moto da cliente Helena registrada em Produtos > Motos" (vendas não são apagadas);
  - a Low Rider S da Helena (placa HIJ8K90) é cadastrada em Produtos > Motos: situação Em preparação, preço de compra R$ 22.000,00, entrada em 15/02/2026, ano, cor e quilometragem em branco (não informados);
  - o preço de compra da moto da loja nº 15 (Low Rider S 2026) passa de R$ 119,95 para R$ 119.950,00.

**Fora do escopo:**
- ligar a moto vendida pela loja às Motos dos clientes (problema B do Explore);
- ligar a conta de usuário ao funcionário da venda (problema C do Explore);
- mudar a regra de faturamento do Painel;
- alterar a OS nº 8 ou a moto da Helena em Motos dos clientes;
- corrigir outros dados antigos (horários importados, OS de 20/02).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `vendas/venda-com-itens`: novo requisito "Tipos de venda" (só BALCAO, PECAS e MOTO; outro tipo é recusado no servidor; vendas antigas de outros tipos continuam consultáveis).

## Impact

- Código: `harley_store/constantes.py` (lista de tipos da venda), `harley_store/vendas_servico.py` (recusa de tipo inválido), `harley_store/state/vendas_state.py` e `harley_store/pages/vendas.py` (lista oferecida na tela); testes em `tests/`.
- Dados (Xano compartilhado entre desenvolvimento e produção): tabela `transacoes` (registro 8), tabela `motos` (um registro novo e o registro 15).
- Painel: o Estoque de Motos passa a incluir R$ 22.000,00 da moto da Helena e os R$ 119.950,00 corretos da moto nº 15. O faturamento não muda, porque a venda nº 8 já ficava fora dele.
- Sem mudança no esquema do Xano (nenhum campo ou tabela nova).
