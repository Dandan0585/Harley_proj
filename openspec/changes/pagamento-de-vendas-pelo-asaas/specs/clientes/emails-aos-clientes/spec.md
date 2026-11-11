## ADDED Requirements

### Requirement: E-mail de confirmação de pagamento
Quando o pagamento de uma venda cobrada pelo Asaas passar a "Pago" e o cliente tiver e-mail, o sistema SHALL enviar ao cliente, pelo SendGrid, um e-mail de confirmação com o número da venda, o valor pago, a forma de pagamento e a data do pagamento. O e-mail MUST ser enviado uma única vez por venda, mesmo que a consulta ao Asaas se repita. Uma venda com a forma "Na loja" MUST NOT gerar esse e-mail. O e-mail segue as regras de remetente, envio em segundo plano e conteúdo dos demais e-mails da loja.

#### Scenario: Boleto pago
- **WHEN** o pagamento do boleto da venda nº 120, de R$ 213,00, é confirmado para um cliente com e-mail
- **THEN** o cliente recebe "Pagamento confirmado - venda nº 120" com o valor, a forma e a data do pagamento

#### Scenario: Consulta repetida
- **WHEN** a consulta ao Asaas roda de novo e encontra a mesma cobrança já paga
- **THEN** nenhum e-mail novo é enviado

#### Scenario: Cliente sem e-mail
- **WHEN** o pagamento de um cliente sem e-mail, que recebeu a cobrança só por SMS, é confirmado
- **THEN** a venda passa a "Pago" e nenhum e-mail é enviado
