## MODIFIED Requirements

### Requirement: Tipos de venda
Ao registrar uma venda, o sistema SHALL oferecer somente os tipos BALCAO, PECAS e MOTO, e MUST recusar outro tipo. O tipo MOTO identifica a venda ligada a uma moto: peças e serviços para a moto do cliente, que MUST entrar no faturamento de produtos, ou a venda de uma moto da loja pelo Balcão, cuja moto conta no faturamento de motos (capacidade `vendas/venda-de-moto-da-loja`). Ao adicionar uma moto da loja à venda, o tipo SHALL passar a ser MOTO.

#### Scenario: Tipos oferecidos na tela
- **WHEN** o funcionário abre o formulário de registro de venda
- **THEN** o campo Tipo oferece apenas BALCAO, PECAS e MOTO

#### Scenario: Venda do tipo MOTO no faturamento
- **WHEN** uma venda do tipo MOTO com um item de R$ 300,00 que não é moto da loja é registrada hoje
- **THEN** o faturamento de produtos de hoje aumenta R$ 300,00 e o faturamento de motos não muda

#### Scenario: Moto da loja adicionada à venda
- **WHEN** o funcionário adiciona uma moto da loja a uma venda do tipo BALCAO
- **THEN** o tipo da venda passa a ser MOTO

#### Scenario: Tipo inválido enviado ao servidor
- **WHEN** chega ao servidor um pedido de registro de venda do tipo COMPRA
- **THEN** a venda não é registrada, nenhum estoque é alterado e o funcionário é informado de que o tipo não é válido

#### Scenario: Venda antiga de tipo que saiu da tela
- **WHEN** alguém consulta uma venda antiga do tipo ORDEM_SERVICO
- **THEN** a venda aparece no histórico com o seu tipo e continua fora do faturamento
