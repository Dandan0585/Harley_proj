## Context

Motivação em proposal.md. A tabela `entrada_mercadoria` tinha só fornecedor, data e valor total; os itens ficam em `itens_compra_estoque`. A equipe pediu para não criar campos desnecessários no Xano; este é o único campo novo, porque o texto escrito pela equipe precisa ser guardado. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Descrição útil desde a primeira compra, sem trabalho extra.

**Non-Goals:**
- Mostrar a descrição no documento impresso da compra.
- Preencher em lote a descrição das compras antigas no banco.

## Decisions

### D1. Um campo de texto opcional
`descricao` em `entrada_mercadoria`, gravado pelo POST (na finalização) e pelo PATCH (na edição). O endpoint PATCH já grava qualquer campo da tabela; o POST e o PUT ganharam a linha do campo.

### D2. Descrição montada pelos itens como alternativa
`descricao_dos_itens()` monta o texto a partir dos itens; é usada para gravar na finalização e para exibir compras sem descrição. Assim as compras antigas não precisam ser alteradas no banco.

### D3. Edição relê o registro inteiro
Antes de gravar, a edição lê a compra direto do Xano (`buscar_direto`) e envia o registro completo, porque o PATCH exige os campos obrigatórios. Se a resposta não trouxer o campo, o app conclui que o Xano ainda não o tem e avisa.

## Risks / Trade-offs

- [Descrição escrita pela equipe fica desatualizada se a compra mudar] → Compras não são editadas depois de gravadas (só excluídas), então isso não ocorre.
