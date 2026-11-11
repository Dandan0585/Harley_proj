## Context

Motivação em proposal.md. Registro retroativo: o código já existia quando este desenho foi escrito (07/10/2026). Os dados vêm das mesmas tabelas das telas (venda, OS, compra e moto, com seus itens e cadastros relacionados).

## Goals / Non-Goals

**Goals:**
- Um documento por tipo de operação, sem gerar arquivos no servidor.

**Non-Goals:**
- Geração de PDF no servidor ou envio do documento por e-mail.
- Nota fiscal (documento sem valor fiscal).

## Decisions

### D1. Página própria, aberta em nova aba
A rota `/imprimir/[doc_tipo]/[doc_id]` é uma página protegida por login. O botão (`components/botao_imprimir.py`) é um link com `is_external`, que abre em nova aba e não interrompe o trabalho na tela de origem.
- *Alternativa:* gerar um PDF no servidor. Rejeitada: exigiria uma biblioteca nova e armazenamento de arquivos; o navegador já salva em PDF.

### D2. Documento descrito de forma genérica
`ImpressaoState` monta, para qualquer tipo, até três grupos de campos, uma tabela de itens, total, observações, termo, faixa de destaque e assinaturas; `pages/impressao.py` só desenha. Um tipo novo é uma função `_montar_<tipo>`.

### D3. Leitura pela cópia em memória
O documento usa `xano.buscar()`, que procura na cópia em memória, para não estourar o limite de requisições (uma OS precisava de 4 buscas avulsas).

## Risks / Trade-offs

- [Dado alterado fora do app] → Pode demorar até 5 minutos para aparecer no documento (mesma regra da cópia em memória).
- [Aparência depende do navegador] → O layout foi feito para A4 e testado com a impressão do navegador.
