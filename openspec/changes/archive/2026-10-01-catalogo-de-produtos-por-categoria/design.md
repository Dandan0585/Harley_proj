## Context

Motivação em proposal.md. Motos e produtos ficam em tabelas diferentes no Xano (`motos` e `produtos`), com cadastros muito diferentes; juntar as tabelas não fazia sentido. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Uma tela a menos, sem perder nenhuma função do cadastro de motos.

**Non-Goals:**
- Unificar as tabelas `motos` e `produtos`.
- Vender motos pela tela de Vendas.

## Decisions

### D1. Aba como filtro de categoria
A aba escolhida é o próprio `filtro_categoria` do `ProdutosState`, com o valor especial "Motos". A página usa `rx.cond(aba_motos, secao_motos(), secao_produtos())`, de modo que cada aba mostra o formulário certo.

### D2. Página de motos vira seção
`pages/motos_loja.py` passou a exportar `secao_motos()` e `dialogo_foto_moto()`, usados pela página de Produtos. O `MotosLojaState` continua o mesmo e é carregado no `on_load` de `/produtos`.

### D3. Endereço antigo preservado
`/motos-loja` é uma página vazia cujo `on_load` redireciona para `/produtos?aba=motos`, para não quebrar favoritos. `ProdutosState.abrir` lê o parâmetro `aba` da URL.

### D4. "Motocicletas" fora das sugestões
A categoria "Motocicletas" saiu das sugestões, e as categorias de moto são recusadas para produto novo, para não haver dois lugares de cadastro de moto.

## Risks / Trade-offs

- [Produto antigo na categoria "Motos"] → Ele não aparece em uma aba própria (o nome é o da aba de motos), mas aparece em "Todas" e continua editável.
