## Why

O OpenSpec 1.14.1, instalado em 09/10/2026, passou a avisar quando o texto de um requisito tem mais de 500 caracteres, e a validação rigorosa (`openspec validate --all --strict`) acusa 5 specs. Requisitos longos misturam várias regras num só bloco, o que dificulta revisar e verificar cada uma.

## What Changes

Cada um dos 5 requisitos longos é reescrito de forma curta. As regras de detalhe passam para requisitos próprios, cada um com o seu cenário. **Nenhum comportamento do sistema muda**: todas as regras e todos os cenários existentes continuam valendo.

| Spec | Requisito longo | Regras que ganham requisito próprio |
|---|---|---|
| `documentos/impressao` | Tipos de documento | Conteúdo dos documentos de operação |
| `motos/estoque-de-motos` | Cadastro da moto da loja | Valores iniciais e localização da moto |
| `painel/visao-financeira` | Faturamento separado entre motos e produtos | Ordens de serviço no faturamento; Cards de faturamento |
| `produtos/catalogo-por-categoria` | Categorias do produto | Motos fora do catálogo de produtos |
| `vendas/venda-com-itens` | Tipos de venda | Recusa de tipo inválido no servidor; Vendas antigas de outros tipos |

**Fora do escopo:**
- qualquer mudança de código, de dados ou de regra de negócio;
- os demais requisitos, que já estão abaixo do limite.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `documentos/impressao`: "Tipos de documento" fica curto; o conteúdo de cada documento de operação vira requisito próprio.
- `motos/estoque-de-motos`: "Cadastro da moto da loja" fica curto; os valores iniciais e a localização viram requisito próprio.
- `painel/visao-financeira`: "Faturamento separado entre motos e produtos" fica curto; as ordens de serviço no faturamento e os cards viram requisitos próprios.
- `produtos/catalogo-por-categoria`: "Categorias do produto" fica curto; a recusa das categorias de moto vira requisito próprio.
- `vendas/venda-com-itens`: "Tipos de venda" fica curto; a recusa no servidor e as vendas antigas viram requisitos próprios.

## Impact

Só os arquivos de spec em `openspec/specs/`. Código, testes e Xano não mudam.
