## Purpose

Organiza o catálogo da loja numa só tela, separado em abas por categoria, incluindo a aba de motos à venda, e define as regras de categoria dos produtos.

## ADDED Requirements

### Requirement: Abas por categoria
A tela Produtos SHALL mostrar uma aba "Todas", com o total de produtos, uma aba para cada categoria (as categorias sugeridas e as que já existem nos produtos), com a quantidade de produtos de cada uma, e a aba "Motos", com a quantidade de motos da loja. Escolher uma aba de categoria MUST mostrar só os produtos dessa categoria.

#### Scenario: Escolher uma categoria
- **WHEN** o funcionário clica na aba "Pneus"
- **THEN** a lista mostra só os produtos da categoria Pneus

### Requirement: Cadastro que acompanha a aba
Na aba Motos, a tela SHALL mostrar o cadastro e a lista de motos da loja; nas demais abas, o cadastro e a lista de produtos. Ao escolher uma aba de categoria, o cadastro de um produto novo MUST já vir com essa categoria preenchida.

#### Scenario: Aba Motos
- **WHEN** o funcionário clica na aba "Motos"
- **THEN** aparecem o formulário de moto e os cartões das motos da loja

#### Scenario: Novo produto na aba Vestuário
- **WHEN** o funcionário está na aba "Vestuário" e começa um produto novo
- **THEN** o campo categoria já vem preenchido com "Vestuário"

### Requirement: Endereços da tela
O endereço `/produtos?aba=motos` SHALL abrir a tela já na aba Motos, e o endereço antigo `/motos-loja` MUST levar para esse mesmo endereço. O item "Produtos" do menu MUST abrir os produtos, mesmo que a última aba vista tenha sido Motos. O menu não tem mais o item "Motos da loja", e os cartões de motos do Painel levam para a aba Motos.

#### Scenario: Favorito antigo
- **WHEN** alguém abre o endereço `/motos-loja`
- **THEN** a tela Produtos abre na aba Motos

#### Scenario: Voltar pelo menu
- **WHEN** o funcionário estava na aba Motos, vai para outra tela e clica em "Produtos" no menu
- **THEN** a tela abre mostrando os produtos

### Requirement: Categorias do produto
A categoria do produto SHALL ser escolhida entre as sugeridas (Peças, Vestuário, Consumíveis, Acessórios, Motores, Pneus, Lubrificantes e Outros) e as já existentes, ou digitada como uma categoria nova. Uma categoria digitada com outra grafia de uma existente (por exemplo, "peças" e "Peças") MUST usar a grafia existente. As categorias "Moto", "Motos", "Motocicleta" e "Motocicletas" MUST ser recusadas para produto, com a orientação de cadastrar motos na aba Motos; um produto antigo que já esteja numa dessas categorias continua podendo ser editado.

#### Scenario: Categoria nova
- **WHEN** o funcionário digita a categoria "Ferramentas", que ainda não existe, e salva o produto
- **THEN** o produto é salvo e a aba "Ferramentas" passa a aparecer

#### Scenario: Produto na categoria Motos
- **WHEN** o funcionário tenta salvar um produto novo com a categoria "Motos"
- **THEN** o produto é recusado com a mensagem de que motos são cadastradas na aba Motos

### Requirement: Busca e estoque baixo
A lista de produtos SHALL permitir buscar por nome ou descrição e mostrar só os produtos com estoque baixo (5 unidades ou menos), que aparecem destacados em vermelho.

#### Scenario: Só estoque baixo
- **WHEN** o funcionário liga "Só estoque baixo"
- **THEN** aparecem só os produtos com 5 unidades ou menos
