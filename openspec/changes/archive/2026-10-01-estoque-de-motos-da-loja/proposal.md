## Why

O estoque de motos à venda precisava refletir o dia a dia da concessionária: motos em preparação, em manutenção, reservadas ou consignadas, com RENAVAM, cilindrada, localização e várias fotos. Também era preciso deixar cadastrar a unidade antes de ela chegar (sem chassi), mas nunca vender sem chassi, porque ele vai no recibo.

Registro retroativo: o módulo de motocicletas foi especificado no repositório anterior (change `cadastro-motocicletas`, arquivada em 16/09/2026, cujos artefatos não estão neste repositório). As mudanças descritas aqui foram feitas na auditoria de 24/09/2026 (commit `018aba5`) e em 01/10/2026 (commit `cb9b8ff`). Esta change documenta o comportamento atual completo.

## What Changes

- Sete situações para a moto, com cor, ícone e texto; só "Vendida" tira a moto do estoque.
- Novos campos: RENAVAM, cilindrada e localização (com sugestões), além de até 8 fotos adicionais com galeria.
- Venda exige o cliente comprador e o chassi; o chassi passa a ser opcional até a venda.
- Gravação sempre do registro completo, para nenhum campo se perder ao editar.
- Procedimento para cadastrar unidades 0 km dos modelos do catálogo, sem placa e sem chassi.
- A tela passa a ser a aba "Motos" de Produtos (change `catalogo-de-produtos-por-categoria`).

## Capabilities

### New Capabilities
- `motos/estoque-de-motos`: cadastro, situações, venda e fotos das motos à venda na loja.

### Modified Capabilities
<!-- Nenhuma neste repositório (a especificação do repositório anterior não foi trazida). -->

## Impact

- **Código**: `harley_store/state/motos_loja_state.py`, `harley_store/pages/motos_loja.py` e `scripts/cadastrar_motos_catalogo.py`.
- **Xano**: campos `renavam`, `cilindrada`, `localizacao` e `fotos` na tabela `motos`; endpoint `motos/foto` para enviar imagens.
