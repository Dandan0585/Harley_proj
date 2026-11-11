## MODIFIED Requirements

### Requirement: Tipos de documento
O sistema SHALL gerar quatro documentos: comprovante de venda, ordem de serviço, entrada de mercadoria e documento da moto da loja. O documento da moto MUST se chamar "Recibo de compra e venda de veículo" quando a moto está Vendida, com o comprador, o valor da venda e o termo de declaração, e "Ficha do veículo" nas demais situações.

#### Scenario: Recibo de moto vendida
- **WHEN** o funcionário imprime uma moto com a situação Vendida
- **THEN** o documento se chama "Recibo de compra e venda de veículo" e traz o comprador, a data e o valor da venda e o termo de declaração

#### Scenario: Ficha de moto em estoque
- **WHEN** o funcionário imprime uma moto que não está vendida
- **THEN** o documento se chama "Ficha do veículo" e traz o preço de venda e a data de entrada

## ADDED Requirements

### Requirement: Conteúdo dos documentos de operação
O comprovante de venda SHALL trazer os itens vendidos, o total e as assinaturas do vendedor e do cliente. A ordem de serviço SHALL trazer a moto, o cliente, o mecânico, as peças e os serviços, e as assinaturas do mecânico e do cliente. A entrada de mercadoria SHALL trazer o fornecedor, os itens comprados e as assinaturas de quem conferiu e do fornecedor.

#### Scenario: Comprovante de venda
- **WHEN** o funcionário imprime uma venda
- **THEN** o documento traz os itens vendidos, o total e os espaços de assinatura do vendedor e do cliente

#### Scenario: Ordem de serviço impressa
- **WHEN** o funcionário imprime uma ordem de serviço
- **THEN** o documento traz a moto, o cliente, o mecânico, as peças e os serviços, e os espaços de assinatura do mecânico e do cliente
