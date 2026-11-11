## Why

A loja precisava entregar ao cliente e ao fornecedor um papel de cada operação (comprovante de venda, ordem de serviço, entrada de mercadoria e o recibo de venda da moto), em vez de anotar à mão.

Registro retroativo: implementado em 23/09/2026 (commit `5b1f108`); o comprovante de venda ganhou os itens e a marca de cancelada na change `vendas-com-itens-e-cancelamento`. Não havia change própria no OpenSpec. Esta change documenta o comportamento em uso.

## What Changes

- Botão "Imprimir" nas listas de Vendas, Ordens de serviço e Compras, e "Ficha" ou "Recibo" nos cartões de motos da loja.
- O documento abre em nova aba, em formato de folha A4, pronto para imprimir ou salvar em PDF pelo navegador.
- Quatro documentos: comprovante de venda, ordem de serviço, entrada de mercadoria e recibo de compra e venda (moto vendida) ou ficha do veículo (demais situações).

## Capabilities

### New Capabilities
- `documentos/impressao`: documentos para impressão gerados a partir dos registros do sistema.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/state/impressao_state.py`, `harley_store/pages/impressao.py`, `harley_store/components/botao_imprimir.py`, rota `/imprimir/[doc_tipo]/[doc_id]` em `harley_store/harley_store.py` e o botão nas telas de Vendas, Ordens de serviço, Compras e Motos.
- **Xano**: só leitura.
- **Dependências**: nenhuma nova.
