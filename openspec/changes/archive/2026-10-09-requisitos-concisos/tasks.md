## 1. Requisitos reescritos

- [x] 1.1 Conferir que cada cenário novo descreve o comportamento atual do código (valores iniciais da moto em `motos_loja_state.novo`, recusa das categorias de moto e exceção do produto antigo em `produtos_state.salvar`, card "hoje" somando motos e produtos em `dashboard_state.resumo_faturamento`, recusa do tipo de venda em `vendas_servico.registrar_venda`); verificar lendo os trechos citados
- [x] 1.2 Validar a change com `openspec validate requisitos-concisos --strict`; verificar que passa
- [x] 1.3 Após o arquivamento, rodar `openspec validate --all --strict`; verificar que todas as specs passam sem aviso de requisito longo (09/10/2026: 19 de 19 specs passam no modo rigoroso)

## 2. Verificação

- [x] 2.1 Rodar todos os testes; verificar que passam (nenhum código mudou)
