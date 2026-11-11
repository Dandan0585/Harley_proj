## Purpose

Mostra a foto oficial de fábrica do modelo para as motos que não têm foto própria, sem atribuir foto a modelos que o sistema não reconhece.

## ADDED Requirements

### Requirement: Modelos com foto oficial
O sistema SHALL ter a foto oficial de fábrica destes modelos: Iron 883, Fat Boy 114, Heritage Classic, Sportster S, Pan America 1250 Special, Street Glide Special, Road Glide Limited, Low Rider S, Breakout 117 e Nightster Special. As fotos MUST ficar no próprio app, sem ocupar o armazenamento do servidor de dados.

#### Scenario: Moto da loja sem foto
- **WHEN** uma moto da loja do modelo "Fat Boy 114" não tem foto enviada
- **THEN** o cartão da moto mostra a foto oficial da Fat Boy 114

### Requirement: Escolha pelo modelo cadastrado
A foto oficial SHALL ser escolhida pelo nome do modelo cadastrado, sem diferenciar maiúsculas, acentos ou o nome da marca antes do modelo. Um modelo que não está na lista MUST ficar sem foto, inclusive modelos de nome parecido.

#### Scenario: Modelo com o nome da marca
- **WHEN** a moto de um cliente está cadastrada como "Harley-Davidson Iron 883"
- **THEN** a miniatura mostra a foto oficial da Iron 883

#### Scenario: Modelo parecido
- **WHEN** uma moto está cadastrada como "Low Rider ST"
- **THEN** ela não recebe a foto da Low Rider S e continua sem foto

### Requirement: Foto enviada tem prioridade
Quando a moto tiver uma foto enviada pela loja, o sistema SHALL mostrar essa foto, e não a oficial.

#### Scenario: Moto com foto própria
- **WHEN** uma moto do modelo "Breakout 117" tem uma foto enviada
- **THEN** o cartão mostra a foto enviada

### Requirement: Exibição da foto oficial
A foto oficial SHALL aparecer inteira, sobre fundo branco, com a indicação "Foto oficial do modelo (Harley-Davidson)" ao passar o mouse. Ela MUST aparecer nos cartões das motos da loja (inclusive na galeria ampliada), na prévia do formulário de moto da loja enquanto o modelo é digitado e nas miniaturas da lista de motos dos clientes.

#### Scenario: Prévia ao digitar o modelo
- **WHEN** o funcionário digita "Nightster Special" no modelo de uma moto da loja nova, sem foto
- **THEN** a prévia da foto do formulário mostra a foto oficial da Nightster Special
