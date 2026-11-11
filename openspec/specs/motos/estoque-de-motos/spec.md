# motos/estoque-de-motos Specification

## Purpose
Controla as motos que a loja compra e revende: cadastro de cada unidade, situação no estoque, fotos e venda para um cliente, separado das motos dos clientes que passam pela oficina.

## Requirements

### Requirement: Cadastro da moto da loja
O cadastro de uma moto da loja SHALL ter marca, modelo, ano, cor, placa, chassi, quilometragem, situação, preços de compra e de venda, datas de entrada e de saída, RENAVAM, cilindrada, localização, cliente (comprador ou reserva), observações e fotos. Marca e modelo MUST ser obrigatórios, e a data de saída MUST NOT ser anterior à data de entrada.

#### Scenario: Cadastrar uma moto
- **WHEN** o funcionário preenche marca e modelo e salva
- **THEN** a moto aparece no estoque com a situação "Em estoque"

#### Scenario: Sem modelo
- **WHEN** o funcionário tenta salvar uma moto sem modelo
- **THEN** o cadastro é recusado com a mensagem "Preencha marca e modelo."

### Requirement: Situações da moto
A moto SHALL ter uma das situações Em estoque, Em preparação, Em manutenção, Reservada, Consignada, Indisponível ou Vendida, exibida no cartão com cor, ícone e texto. Somente a situação Vendida MUST tirar a moto do estoque.

#### Scenario: Moto reservada
- **WHEN** o funcionário marca uma moto como Reservada
- **THEN** a moto continua contando como moto em estoque

### Requirement: Venda da moto
Para marcar uma moto como Vendida, o sistema SHALL exigir o cliente comprador e o chassi. Antes da venda, o chassi pode ficar vazio (por exemplo, unidade que ainda não chegou). Se a data de saída estiver vazia, ela MUST ser preenchida com a data da venda.

#### Scenario: Venda sem chassi
- **WHEN** o funcionário marca como Vendida uma moto sem chassi
- **THEN** a venda é recusada com a mensagem "Para marcar como Vendida, informe o chassi (ele aparece no recibo)."

#### Scenario: Venda sem cliente
- **WHEN** o funcionário marca uma moto como Vendida sem escolher o cliente
- **THEN** a venda é recusada com o pedido para escolher o cliente comprador

#### Scenario: Venda sem data de saída
- **WHEN** o funcionário marca uma moto como Vendida e deixa a data de saída vazia
- **THEN** a moto é gravada com a data de saída de hoje

### Requirement: Placa e chassi únicos
Duas motos da loja MUST NOT ter a mesma placa nem o mesmo chassi. Placa e chassi vazios não contam como repetidos.

#### Scenario: Chassi repetido
- **WHEN** o funcionário salva uma moto com o chassi de outra moto da loja
- **THEN** o cadastro é recusado informando o modelo da moto que já usa esse chassi

#### Scenario: Duas unidades sem chassi
- **WHEN** o funcionário cadastra duas motos sem chassi
- **THEN** as duas são aceitas

### Requirement: Fotos da moto
Cada moto SHALL ter uma foto principal e até 8 fotos adicionais. Qualquer foto adicional MUST poder virar a principal, e as fotos podem ser removidas. O cartão da moto SHALL mostrar a foto principal, o número de fotos e um botão para ampliar, que abre a galeria com todas as fotos. Fotos além do limite de 8 MUST ser ignoradas com aviso.

#### Scenario: Tornar uma foto principal
- **WHEN** o funcionário escolhe "Tornar principal" em uma foto adicional e salva
- **THEN** essa foto passa a ser a principal e a principal anterior passa a ser adicional

### Requirement: Edição sem perda de dados
Salvar a edição de uma moto SHALL manter todos os campos e fotos que o funcionário não alterou.

#### Scenario: Editar só o preço
- **WHEN** o funcionário altera só o preço de venda de uma moto e salva
- **THEN** fotos, RENAVAM, localização e demais campos continuam iguais

### Requirement: Busca e filtro
O estoque de motos SHALL permitir buscar por marca, modelo, placa, chassi, cor, ano ou nome do cliente, e filtrar pela situação.

#### Scenario: Filtrar vendidas
- **WHEN** o funcionário escolhe a situação Vendida no filtro
- **THEN** aparecem só as motos vendidas

### Requirement: Unidades do catálogo
O sistema SHALL oferecer um procedimento, executado com confirmação, que cadastra no estoque, como unidades 0 km, os modelos do catálogo oficial que ainda não estão no estoque, com a cilindrada de fábrica e sem placa e sem chassi. Um modelo que já existe no estoque MUST NOT ser cadastrado de novo.

#### Scenario: Rodar o procedimento duas vezes
- **WHEN** o procedimento é executado depois de já ter cadastrado os modelos
- **THEN** ele informa que não há nada a cadastrar

### Requirement: Valores iniciais e localização da moto
Uma moto nova MUST começar com a marca Harley-Davidson, a situação "Em estoque", a data de entrada de hoje e a localização "Showroom". A localização SHALL sugerir Showroom, Oficina, Pátio, Preparação, Outra loja e Com o cliente, e aceitar outro valor digitado.

#### Scenario: Formulário de moto nova
- **WHEN** o funcionário começa o cadastro de uma moto nova
- **THEN** o formulário já vem com a marca Harley-Davidson, a situação "Em estoque", a data de entrada de hoje e a localização "Showroom"

#### Scenario: Localização digitada
- **WHEN** o funcionário digita a localização "Feira de motos", que não está entre as sugeridas, e salva
- **THEN** a moto é salva com essa localização
