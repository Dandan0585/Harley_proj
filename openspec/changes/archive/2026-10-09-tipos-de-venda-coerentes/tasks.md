## 1. Tipos de venda no código

- [x] 1.1 Trocar `TIPOS_TRANSACAO` por `TIPOS_VENDA = ["BALCAO", "PECAS", "MOTO"]` em `harley_store/constantes.py`, com comentário sobre os tipos antigos, e atualizar `pages/vendas.py` e `state/vendas_state.py`; verificar com `Grep` que `TIPOS_TRANSACAO` não aparece mais em `harley_store/`
- [x] 1.2 Recusar em `vendas_servico.registrar_venda`, antes de qualquer baixa de estoque, o tipo fora de `TIPOS_VENDA` (`FalhaVenda` com mensagem clara); verificar com teste automático que COMPRA e ORDEM_SERVICO são recusados sem chamar o estoque e que BALCAO, PECAS e MOTO passam da conferência
- [x] 1.3 Testar no Painel que uma venda MOTO com item conta em produtos e não em motos, e que vendas antigas COMPRA e ORDEM_SERVICO continuam fora do faturamento; verificar com `tests/test_tipos_de_venda.py` (usa as funções de `tests/test_painel.py`)
- [x] 1.4 Rodar todos os testes e `reflex compile --dry`; verificar que passam

## 2. Correções de dados no Xano

- [x] 2.1 Criar `scripts/corrigir_dados_tipos_de_venda.py` (prévia, confirmação "s", conferência do estado antes de cada correção, design D3 e D4); verificar com uma execução respondendo "n" que a prévia lista as 3 correções e nada é gravado
- [x] 2.2 Rodar o script e confirmar; verificar pela releitura no Xano: venda nº 8 com situação CANCELADA e o motivo; nova moto da loja Low Rider S (HIJ8K90) Em preparação, compra R$ 22.000,00, entrada 15/02/2026; moto nº 15 com preço de compra R$ 119.950,00
- [x] 2.3 Rodar o script de novo; verificar que ele informa que as 3 correções já estão feitas e não grava nada

## 3. Verificação e documentação

- [x] 3.1 Conferir no app (dev): a tela de Vendas oferece só BALCAO, PECAS e MOTO; a venda nº 8 aparece como Cancelada; a moto da Helena aparece em Produtos > Motos; o Estoque de Motos do Painel inclui os valores corrigidos (09/10/2026, com `scripts/iniciar_dev.ps1` respondendo em http://localhost:3001: a página compilada `.web/pages/vendas.js` tem só as opções BALCAO, MOTO e PECAS; nos dados que o app lê, a venda nº 8 está CANCELADA com o motivo e a moto nº 26 está na lista de motos; o Estoque de Motos calculado pela função do Painel passou de R$ 1.959.189,90 para R$ 2.101.019,95, ou seja, +R$ 22.000,00 da moto da Helena e +R$ 119.830,05 da moto nº 15. A conferência visual no navegador fica com o grupo)
- [x] 3.2 Atualizar no README a descrição de Vendas (tipos BALCAO, PECAS e MOTO e o significado de MOTO); verificar lendo a seção "O que o app faz"
