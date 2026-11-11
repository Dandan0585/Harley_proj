## Purpose

Gera documentos em folha A4 a partir dos registros do sistema (venda, ordem de serviço, compra e moto), para imprimir ou salvar em PDF e entregar ao cliente ou ao fornecedor.

## ADDED Requirements

### Requirement: Imprimir a partir das listas
As listas de Vendas, Ordens de serviço e Compras SHALL ter um botão "Imprimir" em cada registro, e os cartões de motos da loja SHALL ter o botão "Recibo" (moto vendida) ou "Ficha" (demais situações). O documento MUST abrir em uma nova aba, sem tirar o funcionário da tela em que está.

#### Scenario: Imprimir uma venda
- **WHEN** o funcionário clica em "Imprimir" em uma venda da lista
- **THEN** o comprovante dessa venda abre em uma nova aba e a tela de Vendas continua aberta

### Requirement: Documento em folha A4
Cada documento SHALL ser montado em formato de folha A4, com o cabeçalho da loja, o título e o número do documento, os grupos de dados (cliente ou fornecedor e detalhes da operação), a tabela de itens, o total, as observações quando houver e os campos de assinatura. O documento MUST poder ser impresso ou salvo em PDF pelo navegador.

#### Scenario: Salvar em PDF
- **WHEN** o funcionário abre um documento e usa a opção de imprimir do navegador
- **THEN** pode imprimir em papel A4 ou salvar como PDF

### Requirement: Tipos de documento
O sistema SHALL gerar quatro documentos:
- comprovante de venda, com os itens vendidos, o total e as assinaturas do vendedor e do cliente;
- ordem de serviço, com a moto, o cliente, o mecânico, as peças e os serviços, e as assinaturas do mecânico e do cliente;
- entrada de mercadoria, com o fornecedor, os itens comprados e as assinaturas de quem conferiu e do fornecedor;
- documento da moto da loja: "Recibo de compra e venda de veículo", com o comprador, o valor da venda e o termo de declaração, quando a moto está Vendida; "Ficha do veículo" nas demais situações.

#### Scenario: Recibo de moto vendida
- **WHEN** o funcionário imprime uma moto com a situação Vendida
- **THEN** o documento se chama "Recibo de compra e venda de veículo" e traz o comprador, a data e o valor da venda e o termo de declaração

#### Scenario: Ficha de moto em estoque
- **WHEN** o funcionário imprime uma moto que não está vendida
- **THEN** o documento se chama "Ficha do veículo" e traz o preço de venda e a data de entrada

### Requirement: Documento inexistente ou inválido
Quando o tipo ou o número do documento for inválido, ou o registro não existir, o sistema SHALL mostrar uma mensagem no lugar do documento, sem erro técnico.

#### Scenario: Registro excluído
- **WHEN** alguém abre o endereço de impressão de uma moto que foi excluída
- **THEN** aparece a mensagem de que a moto não foi encontrada
