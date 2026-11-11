## Why

O grupo não consegue registrar a venda de uma moto em Vendas / Balcão. A tela só lista produtos, e as motos da loja (tabela `motos`) só podem ser vendidas pelo cadastro em Produtos > Motos. Nesse caminho a venda não aparece no histórico de vendas, não gera comprovante de venda e o comprador não fica cadastrado em Motos dos clientes. Para isso, o Balcão precisa acessar o estoque de motos com o preço e os dados de cada moto, e a venda precisa contar uma única vez no Painel.

## What Changes

- O Balcão passa a listar as **motos da loja disponíveis** (todas, exceto Vendida e Indisponível). Ao escolher uma, mostra a foto, o preço de venda e os dados: marca, modelo, ano, cor, placa, chassi, RENAVAM, cilindrada, quilometragem e situação.
- A moto entra na venda como um item, pelo **preço de venda do cadastro**. O servidor relê esse preço e não aceita outro valor. Há no máximo uma moto por venda, e a venda com moto exige o cliente comprador. A moto pode ser vendida junto com produtos e itens avulsos.
- Ao registrar a venda, o servidor confere de novo a moto: ela precisa estar disponível e ter chassi e preço de venda. Depois:
  - marca a moto como **Vendida**, com o cliente e a data de saída;
  - **cadastra a moto em Motos dos clientes** em nome do comprador e liga a venda a esse cadastro. Se já houver um cadastro com o mesmo chassi, ele passa para o comprador. Moto sem placa não é cadastrada, e o funcionário recebe um aviso;
  - envia o e-mail de parabéns ao comprador, como já acontece em Produtos > Motos.
- Se a mesma moto for vendida ao mesmo tempo por dois funcionários, só uma venda é registrada. Se a gravação falhar no meio, nada fica baixado.
- **Painel:** a moto vendida no Balcão conta uma única vez, no faturamento de **Motos**, pelo cadastro da moto. O item da moto não entra em produtos.
- **Cancelamento:** cancelar a venda devolve a moto ao estoque (Em estoque, sem cliente e sem data de saída). O cadastro criado em Motos dos clientes é removido se não tiver ordens de serviço; caso contrário, o sistema pede conferência.
- **Exclusão protegida:** uma moto da loja que aparece em vendas não pode ser excluída.
- **Banco (Xano):** um campo opcional `moto_id` em `itens_transacao` liga o item à moto da loja, com a aprovação do grupo em 13/10/2026. Os endpoints POST e PUT da tabela passam a gravá-lo. O grupo aplica a mudança com `scripts/aplicar_xano.ps1`. Até a aplicação, o servidor recusa a venda de moto com um aviso e não altera nada.

**Fora do escopo:**
- desconto ou preço negociado na moto pelo Balcão (o preço é ajustado antes, no cadastro da moto);
- mais de uma moto por venda;
- mudar a venda de motos pelo cadastro em Produtos > Motos, que continua funcionando como hoje;
- converter vendas antigas de moto;
- novos tipos de venda.

## Capabilities

### New Capabilities

- `vendas/venda-de-moto-da-loja`: venda de uma moto do estoque da loja pelo Balcão, com conferência no servidor, cadastro em Motos dos clientes e cancelamento que devolve a moto.

### Modified Capabilities

- `vendas/venda-com-itens`: o requisito "Tipos de venda" deixa de dizer que a moto da loja só é vendida no cadastro dela.
- `painel/visao-financeira`: o item de moto da loja não conta em produtos; a moto conta uma vez em motos.
- `cadastros/exclusao-protegida`: a moto da loja vendida não pode ser excluída.

## Impact

- Código: `harley_store/vendas_servico.py` (regras da venda e do cancelamento com moto), `harley_store/state/vendas_state.py` e `harley_store/pages/vendas.py` (seleção da moto no Balcão), `harley_store/state/dashboard_state.py` (faturamento), `harley_store/dependencias.py` e `harley_store/state/motos_loja_state.py` (exclusão protegida); testes em `tests/`.
- Xano: espelho em `xano/table/itens_transacao.xs` e nos endpoints `xano/api/harley/itens_transacao_POST.xs` e `itens_transacao/itens_transacao_id_PUT.xs`. O grupo aplica com `scripts/aplicar_xano.ps1`.
- Dados: as vendas de moto gravam registros em `transacoes`, `itens_transacao`, `motos` e `motos_clientes`. Os testes automáticos não usam o Xano real.
