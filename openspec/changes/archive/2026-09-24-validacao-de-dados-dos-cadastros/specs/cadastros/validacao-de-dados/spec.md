## Purpose

Garante que os dados digitados nos cadastros sejam válidos e gravados num formato único, evitando documentos falsos, cadastros duplicados e arquivos que não são imagens.

## ADDED Requirements

### Requirement: CPF e CNPJ válidos e sem duplicidade
O CPF ou CNPJ do cliente e o CNPJ do fornecedor SHALL ser conferidos pelos dígitos verificadores e gravados sempre no mesmo formato (000.000.000-00 ou 00.000.000/0000-00). A duplicidade MUST ser conferida pelos números, independentemente da pontuação digitada.

#### Scenario: CPF com dígito errado
- **WHEN** o funcionário salva um cliente com um CPF cujo dígito verificador está errado
- **THEN** o cadastro é recusado com a mensagem de documento inválido

#### Scenario: Mesmo CPF digitado de outro jeito
- **WHEN** o funcionário cadastra um cliente com um CPF já usado por outro cliente, digitado sem pontuação
- **THEN** o cadastro é recusado com a mensagem de que já existe um cliente com esse CPF/CNPJ, informando o nome dele

### Requirement: E-mail e telefone
O e-mail e o telefone do cliente, quando informados, SHALL ser válidos: o e-mail no formato nome@dominio, e o telefone com DDD e 10 ou 11 dígitos, gravado como (00) 0000-0000 ou (00) 00000-0000. Campos vazios MUST ser aceitos. O e-mail das contas de login segue a mesma regra de formato.

#### Scenario: Telefone sem DDD
- **WHEN** o funcionário informa um telefone com 8 dígitos
- **THEN** o cadastro é recusado com a mensagem de que é preciso informar o DDD e o número

### Requirement: Dados de motos
Nos cadastros de motos, o sistema SHALL aceitar placas no formato antigo (ABC1234) ou Mercosul (ABC1D23), gravadas sem hífen; chassi com 6 a 17 letras e números; RENAVAM com 11 dígitos; ano entre 1903 e o ano seguinte ao atual; quilometragem entre 0 e 2.000.000; e cilindrada entre 50 e 3000 cm³. Placa e chassi MUST ser únicos dentro de cada cadastro de motos.

#### Scenario: Placa em formato inválido
- **WHEN** o funcionário informa a placa "AB12345"
- **THEN** o cadastro é recusado com a mensagem que mostra os formatos aceitos

#### Scenario: Placa digitada com hífen
- **WHEN** o funcionário informa a placa "abc-1d23"
- **THEN** a placa é gravada como "ABC1D23"

### Requirement: Valores numéricos
Preços e valores SHALL aceitar o formato brasileiro ("150.000,00", "R$ 1.234,56") e o formato com ponto decimal ("150000.50"). Quantidades MUST ser números inteiros. Valores negativos MUST ser recusados, e valores acima do limite de cada cadastro (por exemplo, preço de produto acima de R$ 10.000.000) MUST ser recusados com a orientação de conferir o valor.

#### Scenario: Preço com vírgula
- **WHEN** o funcionário digita o preço "1.234,56"
- **THEN** o valor gravado é 1234,56

#### Scenario: Quantidade fracionada
- **WHEN** o funcionário digita a quantidade "1,5"
- **THEN** o valor é recusado

### Requirement: Imagens enviadas
Uma foto enviada SHALL ser aceita somente se a extensão for de imagem permitida na tela (PNG, JPG ou WEBP; GIF também em produtos e motos de clientes), se o arquivo tiver até 5 MB e se o conteúdo do arquivo corresponder à extensão.

#### Scenario: Arquivo renomeado
- **WHEN** o funcionário envia um documento de texto renomeado para "foto.jpg"
- **THEN** o envio é recusado com a mensagem de que o arquivo não é uma imagem válida

#### Scenario: Imagem grande demais
- **WHEN** o funcionário envia uma imagem com mais de 5 MB
- **THEN** o envio é recusado com a mensagem "Imagem muito grande (máximo 5 MB)."
