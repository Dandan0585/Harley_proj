## MODIFIED Requirements

### Requirement: Conteúdo dos documentos de operação
O comprovante de venda SHALL trazer os itens vendidos, o total, a forma e a situação do pagamento e as assinaturas do vendedor e do cliente. A ordem de serviço SHALL trazer a moto, o cliente, o mecânico, as peças e os serviços, e as assinaturas do mecânico e do cliente. A entrada de mercadoria SHALL trazer o fornecedor, os itens comprados e as assinaturas de quem conferiu e do fornecedor.

#### Scenario: Comprovante de venda
- **WHEN** o funcionário imprime uma venda
- **THEN** o documento traz os itens vendidos, o total, a forma e a situação do pagamento e os espaços de assinatura do vendedor e do cliente

#### Scenario: Comprovante de venda com boleto pago
- **WHEN** o funcionário imprime uma venda com boleto já pago
- **THEN** o documento traz a forma "Boleto", a situação "Pago" e a data do pagamento

#### Scenario: Ordem de serviço impressa
- **WHEN** o funcionário imprime uma ordem de serviço
- **THEN** o documento traz a moto, o cliente, o mecânico, as peças e os serviços, e os espaços de assinatura do mecânico e do cliente
