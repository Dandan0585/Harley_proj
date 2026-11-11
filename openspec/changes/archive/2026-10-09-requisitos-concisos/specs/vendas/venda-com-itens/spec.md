## MODIFIED Requirements

### Requirement: Tipos de venda
Ao registrar uma venda, o sistema SHALL oferecer somente os tipos BALCAO, PECAS e MOTO, e MUST recusar outro tipo. O tipo MOTO identifica peças e serviços para a moto do cliente e MUST entrar no faturamento de produtos, não no de motos; a venda de uma moto do estoque da loja é feita no cadastro da própria moto.

#### Scenario: Tipos oferecidos na tela
- **WHEN** o funcionário abre o formulário de registro de venda
- **THEN** o campo Tipo oferece apenas BALCAO, PECAS e MOTO

#### Scenario: Venda do tipo MOTO no faturamento
- **WHEN** uma venda do tipo MOTO com um item de R$ 300,00 é registrada hoje
- **THEN** o faturamento de produtos de hoje aumenta R$ 300,00 e o faturamento de motos não muda

#### Scenario: Tipo inválido enviado ao servidor
- **WHEN** chega ao servidor um pedido de registro de venda do tipo COMPRA
- **THEN** a venda não é registrada, nenhum estoque é alterado e o funcionário é informado de que o tipo não é válido

#### Scenario: Venda antiga de tipo que saiu da tela
- **WHEN** alguém consulta uma venda antiga do tipo ORDEM_SERVICO
- **THEN** a venda aparece no histórico com o seu tipo e continua fora do faturamento

## ADDED Requirements

### Requirement: Recusa de tipo inválido no servidor
O sistema MUST recusar, no servidor, o registro de uma venda com tipo fora de BALCAO, PECAS e MOTO (por exemplo COMPRA ou ORDEM_SERVICO), sem baixar estoque, mesmo que o pedido não venha da tela.

#### Scenario: Tipo ORDEM_SERVICO enviado ao servidor
- **WHEN** chega ao servidor um pedido de registro de venda do tipo ORDEM_SERVICO com um produto em estoque
- **THEN** a venda não é registrada e o estoque do produto não muda

### Requirement: Vendas antigas de outros tipos
Vendas registradas antes com tipos que saíram da tela (COMPRA e ORDEM_SERVICO) MUST continuar consultáveis, com o seu tipo, e com a regra de faturamento que já tinham.

#### Scenario: Venda antiga do tipo COMPRA
- **WHEN** alguém consulta uma venda antiga do tipo COMPRA
- **THEN** a venda aparece no histórico com o tipo COMPRA e fora do faturamento
