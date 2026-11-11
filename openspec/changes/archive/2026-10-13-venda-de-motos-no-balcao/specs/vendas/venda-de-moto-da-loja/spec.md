## ADDED Requirements

### Requirement: Motos da loja no Balcão
A tela de Vendas / Balcão SHALL listar as motos da loja disponíveis para venda, ou seja, todas exceto as Vendidas e as Indisponíveis. Ao escolher uma moto, a tela SHALL mostrar a foto, o preço de venda e os dados da moto: marca, modelo, ano, cor, placa, chassi, RENAVAM, cilindrada, quilometragem e situação.

#### Scenario: Escolher uma moto no Balcão
- **WHEN** o funcionário escolhe no Balcão uma moto Em estoque com preço de venda de R$ 120.000,00
- **THEN** a tela mostra a foto, o preço de R$ 120.000,00, o chassi, a placa, o RENAVAM e os demais dados da moto

#### Scenario: Moto vendida fora da lista
- **WHEN** uma moto da loja está Vendida ou Indisponível
- **THEN** ela não aparece entre as motos do Balcão

### Requirement: Moto como item da venda
A moto SHALL entrar na venda como um item, com quantidade 1 e o preço de venda do cadastro. O preço MUST ser relido pelo servidor, que não aceita outro valor. A venda MUST ter no máximo uma moto da loja e MUST exigir o cliente comprador. A moto pode ser vendida com produtos e itens avulsos na mesma venda. Uma moto sem chassi ou sem preço de venda MUST ser recusada.

#### Scenario: Venda de moto com acessório
- **WHEN** o funcionário adiciona uma moto de R$ 120.000,00 e um capacete de R$ 1.500,00, escolhe o cliente e registra a venda
- **THEN** é registrada uma venda de R$ 121.500,00 com os dois itens

#### Scenario: Moto sem cliente
- **WHEN** o funcionário tenta registrar uma venda com moto sem escolher o cliente
- **THEN** a venda não é registrada e o sistema pede para escolher o cliente comprador

#### Scenario: Duas motos na mesma venda
- **WHEN** o funcionário tenta adicionar uma segunda moto à venda
- **THEN** o sistema recusa e informa que só é possível uma moto da loja por venda

#### Scenario: Moto sem chassi
- **WHEN** o funcionário tenta vender uma moto que não tem chassi
- **THEN** a venda é recusada com o pedido para informar o chassi no cadastro da moto

### Requirement: Registro da venda da moto
Ao registrar a venda, o servidor MUST conferir de novo que a moto está disponível. A moto SHALL então ser marcada como Vendida, com o cliente comprador e a data de saída da venda. O comprador com e-mail SHALL receber o e-mail de parabéns pela compra. Se a mesma moto for vendida ao mesmo tempo por dois funcionários, só uma venda MUST ser registrada. Se a gravação falhar no meio, nenhum estoque MUST ficar baixado e a moto MUST NOT ficar Vendida.

#### Scenario: Venda registrada
- **WHEN** uma venda com moto é registrada para o cliente João
- **THEN** a moto fica Vendida para João, com a data de saída de hoje, e sai das motos disponíveis no Balcão

#### Scenario: Disputa pela mesma moto
- **WHEN** dois funcionários registram, ao mesmo tempo, vendas da mesma moto
- **THEN** apenas uma venda é registrada, e a outra é recusada informando que a moto já foi vendida

#### Scenario: Banco ainda sem o vínculo da moto
- **WHEN** o campo que liga o item à moto ainda não foi aplicado no Xano
- **THEN** a venda com moto é recusada sem alterar nada, com o aviso para aplicar a atualização do banco

### Requirement: Moto cadastrada nas motos do cliente
A venda de uma moto da loja SHALL cadastrar a moto em Motos dos clientes, em nome do comprador, e ligar a venda a esse cadastro. Se já existir um cadastro com o mesmo chassi, ele SHALL passar para o comprador. Uma moto sem placa MUST NOT ser cadastrada, e o funcionário SHALL ser avisado para cadastrá-la depois do emplacamento.

#### Scenario: Moto emplacada
- **WHEN** é vendida uma moto com placa ABC1D23 para o cliente João
- **THEN** a moto aparece em Motos dos clientes em nome de João, com a placa e o chassi

#### Scenario: Moto 0 km sem placa
- **WHEN** é vendida uma moto sem placa
- **THEN** a venda é registrada, e o sistema avisa que a moto deve ser cadastrada em Motos dos clientes depois do emplacamento

### Requirement: Cancelamento da venda com moto
Cancelar uma venda com moto da loja SHALL devolver a moto ao estoque, na situação Em estoque, sem cliente e sem data de saída. A moto cadastrada em Motos dos clientes por essa venda SHALL ser removida quando não tiver ordens de serviço. Se a moto ou o cadastro tiverem sido alterados depois da venda, o sistema MUST avisar para conferir manualmente.

#### Scenario: Cancelar venda de moto
- **WHEN** é cancelada a venda de uma moto ainda Vendida para o mesmo cliente
- **THEN** a moto volta a Em estoque, sem cliente, aparece de novo no Balcão e sai do faturamento de motos

#### Scenario: Moto com ordem de serviço
- **WHEN** é cancelada a venda de uma moto cujo cadastro de cliente já tem uma ordem de serviço
- **THEN** a moto volta ao estoque, o cadastro do cliente é mantido e o sistema avisa para conferi-lo
