# Proposal

## Why

Hoje cada venda guarda só o valor total (tabela `transacoes`, sem itens). Por isso:
- uma venda só pode ter um produto;
- não se sabe depois o que foi vendido;
- "cancelar" significa **apagar** o registro, sem histórico;
- o estoque **não volta** quando uma venda é desfeita;
- não é possível cancelar várias vendas de uma vez.

Com vários funcionários usando o sistema ao mesmo tempo (change `acesso-em-rede-local`), duas vendas simultâneas do mesmo produto podem ainda perder uma das baixas de estoque, porque a baixa lê o saldo, subtrai e grava o registro inteiro.

O usuário decidiu que uma venda cancelada deve continuar registrada, marcada como cancelada, e não ser apagada.

## What Changes

- Uma venda passa a ter **vários itens** (carrinho): produtos do estoque, com quantidade e preço unitário, e itens avulsos (descrição + valor, sem estoque, por exemplo mão de obra ou uma moto). O total da venda é a soma dos itens.
- Os itens de cada venda passam a ser **gravados** e aparecem na consulta da venda e no comprovante impresso.
- O **cancelamento** substitui a exclusão, e a mudança é **BREAKING** para quem usava "Excluir" em vendas:
  - a venda permanece no histórico, com a situação "Cancelada", data do cancelamento e motivo (opcional);
  - vendas canceladas deixam de contar no faturamento (painel e gráfico);
  - os produtos dos itens voltam ao estoque automaticamente.
- É possível **selecionar várias vendas e cancelá-las de uma vez**, com uma única confirmação.
- As baixas e devoluções de estoque passam a ser **protegidas contra operações simultâneas** no mesmo produto; nenhuma baixa se perde.
- Uma venda não pode ser cancelada duas vezes, e o estoque não é devolvido em dobro.
- Vendas antigas, registradas antes desta change e portanto sem itens gravados, continuam visíveis e podem ser canceladas. Nesse caso nada volta ao estoque, porque não se sabe o que foi vendido, e o sistema avisa isso.
- O comprovante de venda impresso lista os itens e mostra claramente quando a venda está cancelada.

Fora do escopo:
- ligar a venda de uma moto da loja (tela Motos da loja) à venda;
- restringir o cancelamento ao administrador (entra na change `perfis-de-acesso`);
- mover a lógica de venda para funções do Xano;
- editar uma venda já registrada.

## Capabilities

### New Capabilities
- `vendas/venda-com-itens`: registro de uma venda com vários itens (produtos do estoque e itens avulsos), cálculo do total, baixa de estoque protegida contra concorrência e consulta dos itens gravados.
- `vendas/cancelamento-de-vendas`: cancelamento que preserva o histórico, marca a situação, registra data e motivo, devolve o estoque, exclui a venda do faturamento e permite cancelar várias vendas de uma vez.

### Modified Capabilities
<!-- Nenhuma: ainda não há specs arquivadas no projeto. -->

## Impact

- **Banco (Xano), por ação manual do usuário no painel do Xano**, porque o plano Free não permite criar tabelas pela API:
  - nova tabela `itens_transacao`, com endpoints de CRUD no mesmo grupo de API das demais tabelas;
  - novos campos em `transacoes`: `status`, `data_cancelamento` e `motivo_cancelamento`;
  - vendas existentes ficam sem `status` e são tratadas como ativas.
- **Código**:
  - `harley_store/state/vendas_state.py` e `harley_store/pages/vendas.py`: carrinho, cancelamento, seleção múltipla e situação na lista;
  - `harley_store/state/dashboard_state.py`: faturamento ignora canceladas;
  - `harley_store/state/impressao_state.py`: itens e marca de cancelada no comprovante;
  - `harley_store/xano_client.py` ou um módulo novo: trava por produto para as operações de estoque;
  - espelho `xano/table/`: `transacoes.xs` e o novo `itens_transacao.xs`.
- **Usuários**: o botão "Excluir" das vendas passa a ser "Cancelar"; vendas não são mais apagadas pelo app.
- **Dados**: nenhum dado existente é alterado ou perdido.
- **Dependências**: nenhuma nova.
