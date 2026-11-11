## MODIFIED Requirements

### Requirement: Categorias do produto
A categoria do produto SHALL ser escolhida entre as sugeridas (Peças, Vestuário, Consumíveis, Acessórios, Motores, Pneus, Lubrificantes e Outros) e as já existentes, ou digitada como uma categoria nova. Uma categoria digitada com outra grafia de uma existente (por exemplo, "peças" e "Peças") MUST usar a grafia existente. Categorias de moto MUST ser recusadas para produto.

#### Scenario: Categoria nova
- **WHEN** o funcionário digita a categoria "Ferramentas", que ainda não existe, e salva o produto
- **THEN** o produto é salvo e a aba "Ferramentas" passa a aparecer

#### Scenario: Produto na categoria Motos
- **WHEN** o funcionário tenta salvar um produto novo com a categoria "Motos"
- **THEN** o produto é recusado com a mensagem de que motos são cadastradas na aba Motos

## ADDED Requirements

### Requirement: Motos fora do catálogo de produtos
As categorias "Moto", "Motos", "Motocicleta" e "Motocicletas" MUST ser recusadas para produto, com a orientação de cadastrar motos na aba Motos. Um produto antigo que já esteja numa dessas categorias SHALL continuar podendo ser editado.

#### Scenario: Categoria Motocicleta
- **WHEN** o funcionário tenta salvar um produto novo com a categoria "Motocicleta"
- **THEN** o produto é recusado com a orientação de cadastrar motos na aba Motos

#### Scenario: Produto antigo na categoria Motos
- **WHEN** o funcionário edita o preço de um produto antigo que já está na categoria "Motos"
- **THEN** a alteração é salva
