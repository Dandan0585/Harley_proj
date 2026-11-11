## Why

Produtos e motos ficavam em telas separadas, e a tela de Produtos mostrava tudo misturado, com o filtro de categoria escondido num menu. A equipe pediu, em sala de aula, para juntar as duas telas e organizar o catálogo por categoria, com uma aba de motos que mantivesse o cadastro completo de moto, para ter uma tela a menos para gerenciar.

Registro retroativo: as categorias sugeridas e o filtro vieram da auditoria de 24/09/2026 (commit `018aba5`); as abas, a aba Motos e o fim da página "Motos da loja" foram feitos em 01/10/2026 (commit `cb9b8ff`). Esta change documenta o comportamento em uso.

## What Changes

- A tela Produtos passa a ter abas: "Todas", uma por categoria (com a quantidade de produtos) e "Motos".
- Na aba Motos, o formulário e a lista viram os de moto (change `estoque-de-motos-da-loja`); nas demais, os de produto.
- **BREAKING**: a página "Motos da loja" sai do menu; o endereço antigo `/motos-loja` leva para a aba Motos.
- Escolher uma categoria já preenche a categoria do produto novo; uma categoria nova é só digitada.
- Produto não pode usar a categoria "Motos" ou "Motocicletas", porque motos são cadastradas na aba Motos.

## Capabilities

### New Capabilities
- `produtos/catalogo-por-categoria`: organização do catálogo da loja em abas por categoria, incluindo a aba de motos, e as regras de categoria do produto.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/state/produtos_state.py`, `harley_store/pages/produtos.py`, `harley_store/pages/motos_loja.py` (vira uma seção), `harley_store/harley_store.py` (rotas), `harley_store/components/layout.py` (menu) e `harley_store/pages/dashboard.py` (links).
- **Xano**: nenhuma mudança.
