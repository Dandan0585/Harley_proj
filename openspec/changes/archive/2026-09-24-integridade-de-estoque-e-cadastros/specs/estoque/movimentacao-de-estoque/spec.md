## Purpose

Garante que o saldo de cada produto esteja sempre correto, mesmo com várias operações ao mesmo tempo, e que cada alteração do saldo fique registrada e possa ser consultada.

## ADDED Requirements

### Requirement: Movimentações aplicadas sobre o saldo atual
Toda alteração do saldo de um produto (venda, cancelamento de venda, peças de uma OS, exclusão de OS, compra, exclusão de compra e ajuste na edição do produto) SHALL partir do saldo atual lido do servidor de dados no momento da operação. Operações simultâneas no mesmo produto MUST NOT fazer uma movimentação se perder.

#### Scenario: Duas operações ao mesmo tempo
- **WHEN** uma compra e uma venda do mesmo produto são registradas ao mesmo tempo
- **THEN** o saldo final reflete as duas movimentações

### Requirement: Tudo ou nada, sem saldo negativo
Uma operação que movimenta vários produtos SHALL ser recusada inteira, sem alterar nenhum saldo, quando deixaria algum produto com saldo negativo, informando quais produtos não têm estoque suficiente. Se uma gravação falhar no meio, as movimentações já aplicadas MUST ser desfeitas.

#### Scenario: OS com peça sem estoque
- **WHEN** um funcionário abre uma OS com duas peças e uma delas não tem estoque suficiente
- **THEN** a OS não é gravada, nenhum saldo muda e aparece "Estoque insuficiente" com o nome da peça

#### Scenario: Falha no meio da operação
- **WHEN** a gravação do segundo produto de uma operação falha
- **THEN** o saldo do primeiro produto volta ao valor anterior

### Requirement: Edição do produto sem apagar movimentações
Ao salvar a edição de um produto, o sistema SHALL aplicar ao saldo atual apenas a diferença entre o estoque digitado e o saldo de quando a edição foi aberta. Se houve movimentações enquanto o formulário estava aberto, o funcionário MUST ser avisado do saldo final; se o ajuste deixaria o saldo negativo, a edição MUST ser recusada.

#### Scenario: Venda durante a edição
- **WHEN** um produto com 10 unidades é aberto para edição, 2 unidades são vendidas e o funcionário salva o formulário com o estoque ainda em 10
- **THEN** o saldo fica em 8 e o funcionário é avisado de que houve movimentação enquanto o formulário estava aberto

### Requirement: Compras e ordens de serviço movimentam o estoque
Registrar uma compra SHALL somar os itens ao estoque, e excluir uma compra SHALL retirar do estoque o que ela somou. A exclusão da compra MUST ser recusada, sem alterar nada, quando parte dos produtos já saiu do estoque. Abrir uma OS SHALL baixar as peças lançadas, e excluir uma OS SHALL devolvê-las ao estoque.

#### Scenario: Excluir compra já vendida
- **WHEN** um funcionário tenta excluir uma compra cujos produtos já foram vendidos
- **THEN** a exclusão é recusada, com a lista dos produtos, e nada é alterado

#### Scenario: Excluir uma OS
- **WHEN** um funcionário exclui uma OS que usou peças
- **THEN** as peças voltam ao estoque

### Requirement: Histórico de movimentações
Cada movimentação de estoque SHALL ser registrada com data e hora, origem (venda, venda cancelada, OS, OS excluída, compra, compra excluída, ajuste manual ou cadastro do produto), número do documento, quantidade (positiva para entrada, negativa para saída), saldo após a movimentação e usuário. O histórico de um produto SHALL poder ser consultado na tela Produtos, com as 100 movimentações mais recentes. Uma falha ao registrar o histórico MUST NOT desfazer nem impedir a operação.

#### Scenario: Consultar o histórico
- **WHEN** o funcionário clica em "Histórico" em um produto
- **THEN** aparece a lista das movimentações do produto, da mais recente para a mais antiga, com origem, documento, quantidade, saldo e usuário

#### Scenario: Histórico indisponível
- **WHEN** o registro do histórico falha durante uma venda
- **THEN** a venda é concluída normalmente
