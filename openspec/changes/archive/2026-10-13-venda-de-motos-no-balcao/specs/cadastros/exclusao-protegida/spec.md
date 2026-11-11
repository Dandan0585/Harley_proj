## MODIFIED Requirements

### Requirement: Exclusão recusada para cadastro em uso
A exclusão de um cliente, fornecedor, funcionário, moto de cliente, moto da loja ou produto SHALL ser recusada quando houver registros ligados a ele, com uma mensagem que diz onde ele é usado:
- cliente: motos de clientes, vendas e motos da loja;
- fornecedor: compras;
- funcionário: vendas e ordens de serviço;
- moto de cliente: ordens de serviço e vendas;
- moto da loja: vendas;
- produto: vendas, ordens de serviço e compras.

#### Scenario: Cliente com vendas
- **WHEN** um funcionário tenta excluir um cliente que tem vendas
- **THEN** a exclusão é recusada com a mensagem de que há registros ligados a ele em vendas

#### Scenario: Moto da loja vendida no Balcão
- **WHEN** um funcionário tenta excluir uma moto da loja que aparece em uma venda
- **THEN** a exclusão é recusada com a mensagem de que há registros ligados em vendas

#### Scenario: Cadastro sem uso
- **WHEN** um funcionário exclui um fornecedor que não aparece em nenhuma compra
- **THEN** o fornecedor é excluído
