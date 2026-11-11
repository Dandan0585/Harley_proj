## Purpose

Impede a exclusão de cadastros que ainda são usados em vendas, ordens de serviço, compras ou motos, para que o histórico nunca aponte para um registro inexistente.

## ADDED Requirements

### Requirement: Exclusão recusada para cadastro em uso
A exclusão de um cliente, fornecedor, funcionário, moto de cliente ou produto SHALL ser recusada quando houver registros ligados a ele, com uma mensagem que diz onde ele é usado:
- cliente: motos de clientes, vendas e motos da loja;
- fornecedor: compras;
- funcionário: vendas e ordens de serviço;
- moto de cliente: ordens de serviço e vendas;
- produto: vendas, ordens de serviço e compras.

#### Scenario: Cliente com vendas
- **WHEN** um funcionário tenta excluir um cliente que tem vendas
- **THEN** a exclusão é recusada com a mensagem de que há registros ligados a ele em vendas

#### Scenario: Cadastro sem uso
- **WHEN** um funcionário exclui um fornecedor que não aparece em nenhuma compra
- **THEN** o fornecedor é excluído

### Requirement: Produto fora de circulação
Quando a exclusão de um produto for recusada por estar em uso, a mensagem SHALL orientar a deixar o estoque em 0 para tirá-lo de circulação.

#### Scenario: Produto já vendido
- **WHEN** um funcionário tenta excluir um produto que aparece em vendas
- **THEN** a mensagem informa onde ele aparece e orienta a deixar o estoque em 0

### Requirement: Na dúvida, não excluir
Se não for possível conferir os registros ligados, por falta de conexão com o servidor de dados, a exclusão MUST NOT acontecer.

#### Scenario: Sem conexão durante a exclusão
- **WHEN** a conferência dos registros ligados falha por falta de conexão
- **THEN** o cadastro não é excluído e aparece a mensagem de falta de conexão
