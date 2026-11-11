## 1. Banco (espelho do Xano)

- [x] 1.1 Acrescentar `int moto_id? { table = "motos" }` em `xano/table/itens_transacao.xs` e `moto_id: $input.moto_id` nos endpoints `xano/api/harley/itens_transacao_POST.xs` e `itens_transacao/itens_transacao_id_PUT.xs`; verificar lendo os 3 arquivos (a aplicação no Xano fica com o grupo: `.\scripts\aplicar_xano.ps1`) (13/10/2026: os 3 arquivos conferidos no `git diff`; a aplicação no Xano está pendente com o grupo)

## 2. Regras no servidor

- [x] 2.1 Em `vendas_servico.py`, criar as funções puras `problema_moto`, `descricao_moto`, `moto_vendida` e `moto_devolvida`, e em `registrar_venda` aceitar um item com `id_moto` (uma moto por venda, exige cliente, preço e descrição relidos do Xano, trava por moto, conferência do campo `moto_id`, moto marcada como Vendida com compensação em caso de falha, retorno `(id, avisos)`); verificar com teste automático (moto simulada, sem o Xano) (`tests/test_venda_de_moto.py`: regras, venda com acessório, sem cliente, duas motos, moto já vendida, disputa, Xano sem o campo antes e depois de gravar)
- [x] 2.2 Cadastrar ou transferir a moto em `motos_clientes` pelo chassi, ligar a venda (`id_moto_cliente`), avisar quando a moto não tiver placa e enviar o e-mail de parabéns; verificar com teste automático (testes de venda com acessório, moto sem placa e cadastro com o mesmo chassi)
- [x] 2.3 Em `cancelar_venda`, devolver a moto ao estoque (só se ainda estiver Vendida para o mesmo cliente) e remover o cadastro da moto do cliente quando não houver OS; verificar com teste automático (testes de cancelamento: devolução, moto com OS e moto alterada depois da venda)
- [x] 2.4 No Painel (`lancamentos_faturamento`), ignorar o item com `moto_id`; verificar com teste do cenário "Moto vendida no Balcão" (motos R$ 120.000,00, produtos R$ 1.500,00, hoje R$ 121.500,00)
- [x] 2.5 Incluir `motos` em `dependencias.REFERENCIAS` (itens_transacao.moto_id) e usar `em_uso` em `MotosLojaState.excluir`; verificar com teste automático da referência

## 3. Tela de Vendas / Balcão

- [x] 3.1 Em `vendas_state.py`, carregar as motos disponíveis, mostrar os dados da moto escolhida, adicioná-la ao carrinho (tipo MOTO, no máximo uma) e exigir o cliente; em `pages/vendas.py`, adicionar a seleção da moto com foto, preço e dados, e o selo "moto" no carrinho; verificar com `reflex compile --dry` (13/10/2026: "App compiled successfully". A conferência visual no navegador e o teste com uma moto marcada como TESTE ficam com o grupo, depois de aplicar o campo no Xano)

## 4. Verificação e documentação

- [x] 4.1 Rodar `.venv\Scripts\python.exe -m unittest discover -s tests -t .` e `reflex compile --dry`; verificar que passam (13/10/2026: 70 testes OK, 16 deles novos; compilação OK)
- [x] 4.2 Atualizar `README.md` e `docs/` (Vendas / Balcão vende motos da loja; campo `moto_id`); verificar lendo as seções (README "O que o app faz", `docs/project-overview.md` seção 6 e `docs/domain-model.md` Moto da loja e Venda)
