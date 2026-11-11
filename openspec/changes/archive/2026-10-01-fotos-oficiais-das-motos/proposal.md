## Why

A maioria das motos da loja e das motos dos clientes não tinha foto, e a equipe pediu as imagens oficiais dos modelos, sem inventar fotos para motos que não existem no cadastro.

Registro retroativo: implementado em 01/10/2026 (commit `cb9b8ff`). Esta change documenta o comportamento em uso.

## What Changes

- Fotos de fábrica (site oficial da Harley-Davidson) de 10 modelos guardadas no próprio app.
- Moto sem foto enviada passa a mostrar a foto oficial do modelo cadastrado, nas motos da loja e nas motos dos clientes.
- Modelo não reconhecido continua sem foto; a foto enviada pela loja sempre tem prioridade.

## Capabilities

### New Capabilities
- `motos/fotos-oficiais`: escolha e exibição da foto oficial do modelo para motos sem foto própria.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: novo `harley_store/fotos_oficiais.py`; `state/motos_loja_state.py`, `pages/motos_loja.py`, `state/motos_state.py` e `pages/motos.py`.
- **Arquivos**: 10 imagens em `assets/motos/` (cerca de 4 MB no total).
- **Xano**: nenhuma mudança e nenhum uso do armazenamento.
