## 1. Categorias

- [x] 1.1 Sugerir as categorias padrão, aceitar categoria nova e reaproveitar a grafia existente; feito em 24/09/2026 (commit `018aba5`) e verificado no código de `produtos_state.py`
- [x] 1.2 Recusar as categorias de moto para produto novo, mantendo editável o produto antigo; feito em 01/10/2026 (commit `cb9b8ff`) e verificado no código (`_categoria_lida`)

## 2. Abas e aba Motos

- [x] 2.1 Criar as abas com a quantidade por categoria e a aba Motos com a quantidade de motos; feito em 01/10/2026 e verificado no código de `pages/produtos.py`
- [x] 2.2 Transformar a página de motos em seção e mostrá-la na aba Motos; verificado no código e no uso real (motos cadastradas pela aba Motos de 05 a 07/10/2026)
- [x] 2.3 Redirecionar `/motos-loja`, abrir a aba pelo parâmetro `aba`, tirar "Motos da loja" do menu e apontar os cartões do Painel para a aba Motos; verificado no código de `harley_store.py`, `layout.py` e `pages/dashboard.py`
- [x] 2.4 Fazer o item "Produtos" do menu voltar aos produtos depois de usar a aba Motos; corrigido em 01/10/2026 e verificado no código (`ProdutosState.abrir`)
- [x] 2.5 Compilar o app; verificado em 07/10/2026 (`reflex compile` sem erros)
