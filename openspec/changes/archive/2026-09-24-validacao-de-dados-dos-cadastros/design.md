## Context

Motivação em proposal.md. Cada tela tinha conferências próprias, ou nenhuma. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Uma única implementação de cada regra, usada por todas as telas.

**Non-Goals:**
- Corrigir os registros antigos em lote.
- Consultar órgãos externos (Receita Federal, Detran).

## Decisions

### D1. Módulo compartilhado `validacao.py`
Funções puras, sem acesso ao Xano: `validar_cpf_cnpj`, `validar_cnpj`, `formatar_cpf_cnpj`, `validar_email`, `validar_telefone`, `formatar_telefone`, `numero`, `inteiro`, `moeda` e `validar_imagem`. As validações de placa, chassi, RENAVAM e faixas de valores ficam nos states de motos, que usam `numero` e `inteiro`.

### D2. Formato único na gravação
CPF, CNPJ e telefone são gravados formatados, e a placa é gravada sem hífen e em maiúsculas; a duplicidade é conferida pelos dígitos (`somente_digitos`). Assim, a busca e a checagem de duplicidade não dependem de como o funcionário digitou.

### D3. Imagem conferida pela assinatura
`validar_imagem` confere extensão, tamanho e os primeiros bytes do arquivo (assinatura de PNG, JPEG, WEBP ou GIF).
- *Alternativa:* confiar na extensão. Rejeitada: qualquer arquivo renomeado passaria.

## Risks / Trade-offs

- [Registros antigos fora do padrão] → São conferidos e formatados quando forem salvos de novo.
