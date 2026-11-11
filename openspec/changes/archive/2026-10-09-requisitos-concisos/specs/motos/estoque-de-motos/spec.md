## MODIFIED Requirements

### Requirement: Cadastro da moto da loja
O cadastro de uma moto da loja SHALL ter marca, modelo, ano, cor, placa, chassi, quilometragem, situação, preços de compra e de venda, datas de entrada e de saída, RENAVAM, cilindrada, localização, cliente (comprador ou reserva), observações e fotos. Marca e modelo MUST ser obrigatórios, e a data de saída MUST NOT ser anterior à data de entrada.

#### Scenario: Cadastrar uma moto
- **WHEN** o funcionário preenche marca e modelo e salva
- **THEN** a moto aparece no estoque com a situação "Em estoque"

#### Scenario: Sem modelo
- **WHEN** o funcionário tenta salvar uma moto sem modelo
- **THEN** o cadastro é recusado com a mensagem "Preencha marca e modelo."

## ADDED Requirements

### Requirement: Valores iniciais e localização da moto
Uma moto nova MUST começar com a marca Harley-Davidson, a situação "Em estoque", a data de entrada de hoje e a localização "Showroom". A localização SHALL sugerir Showroom, Oficina, Pátio, Preparação, Outra loja e Com o cliente, e aceitar outro valor digitado.

#### Scenario: Formulário de moto nova
- **WHEN** o funcionário começa o cadastro de uma moto nova
- **THEN** o formulário já vem com a marca Harley-Davidson, a situação "Em estoque", a data de entrada de hoje e a localização "Showroom"

#### Scenario: Localização digitada
- **WHEN** o funcionário digita a localização "Feira de motos", que não está entre as sugeridas, e salva
- **THEN** a moto é salva com essa localização
