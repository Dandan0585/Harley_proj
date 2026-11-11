## 0. Pré-requisitos (grupo)

- [x] 0.1 Aprovar a change, incluindo os campos novos em `transacoes` (design D3) e as perguntas em aberto do design (11/11/2026: aprovada pelo grupo, com as sugestões da proposta; ver "Decisões do grupo" no design)
- [x] 0.2 Criar a conta no Asaas Sandbox, gerar a chave de API e colocar `ASAAS_API_KEY` e `ASAAS_AMBIENTE=sandbox` no `.env` de desenvolvimento e de produção (a chave nunca vai para o git nem para o chat) (11/11/2026: chave no `.env` de desenvolvimento, aceita pelo Asaas no `scripts\testar_asaas.py`; o `.env` da produção fica com o grupo)

## 1. Banco (espelho do Xano)

- [x] 1.1 Acrescentar `forma_pagamento`, `situacao_pagamento`, `asaas_cobranca_id`, `link_cobranca` e `data_pagamento` (opcionais) em `xano/table/transacoes.xs` e nos endpoints `xano/api/harley/transacoes_POST.xs`, `transacoes/transacoes_id_PUT.xs` e `transacoes/transacoes_id_PATCH.xs`; verificar lendo os arquivos (a aplicação no Xano fica com o grupo: `.\scripts\aplicar_xano.ps1`) (11/11/2026: tabela, POST e PUT conferidos; o PATCH grava os campos recebidos (`$input|pick`) e não precisou mudar. Aplicado no workspace HARLEY (168750) com o perfil "Harley" do CLI. A prévia mostrou só os 5 ADD_FIELD em `transacoes` e os endpoints POST e PUT; depois da aplicação, ela ficou em "No changes to push")

## 2. Integração com o Asaas

- [x] 2.1 Criar `harley_store/asaas_client.py` (configuração pelo `.env`, cabeçalhos `access_token` e `User-Agent`, clientes e cobranças, erros em português, chave fora do log); verificar com teste automático usando `httpx.MockTransport` (`TestClienteAsaas`: endereço do Sandbox, cabeçalhos, erro em português sem a chave, chave recusada, sem configuração)
- [x] 2.2 Criar `harley_store/pagamentos_servico.py` com as funções puras do design D2 e `gerar_cobranca(venda_id)` (reaproveita a cobrança pela referência, procura ou cria o cliente pelo CPF/CNPJ); verificar com testes automáticos (tradução dos status, telefone celular e fixo, vencimento, cliente sem dados, nova tentativa sem duplicar) (`TestRegrasPuras` e `TestRegistroComPagamento`)
- [x] 2.3 Criar `atualizar_pagamentos()` (vendas em AGUARDANDO/VENCIDO, grava só quando muda, trava por venda, e-mail só na passagem para PAGO depois de gravar) e registrá-la como tarefa periódica em `harley_store/harley_store.py`; verificar com testes automáticos (pago, vencido e depois pago, consulta repetida sem e-mail, falha ao gravar sem e-mail) (`TestConfirmacao`)

## 3. Vendas e cancelamento

- [x] 3.1 Em `vendas_servico.registrar_venda`, aceitar `forma_pagamento` e `vencimento`, validar antes do estoque, conferir se o Xano tem os campos novos, gravar a forma e a situação e chamar `gerar_cobranca` sem desfazer a venda em caso de falha; verificar com teste automático (`TestRegistroComPagamento`: forma inválida, sem cliente e vencimento no passado sem baixar estoque; falha no Asaas mantém a venda)
- [x] 3.2 Fazer `_marcar_cancelada` e a ligação com `id_moto_cliente` enviarem os campos de pagamento (PATCH completo); em `cancelar_venda`, cancelar a cobrança em aberto e avisar quando a venda estiver paga ou o Asaas falhar; verificar com teste automático (o cancelamento mantém os dados do pagamento) (`TestCancelamento`; os dois pontos já copiavam o registro inteiro, e `_marcar_cancelada` passou a devolver a venda gravada)

## 4. E-mail

- [x] 4.1 Criar `email_clientes.pagamento_confirmado(...)` com o modelo da loja e a versão em texto; verificar com teste automático (conteúdo e escape do nome) (`TestEmailDeConfirmacao`)

## 5. Telas (Reflex)

- [x] 5.1 Em `vendas_state.py` e `pages/vendas.py`: seletor de forma de pagamento (só "Na loja" sem Asaas), vencimento, selo da situação, link "Abrir cobrança", botões "Gerar cobrança de novo" e "Atualizar pagamentos"; verificar com `reflex compile --dry` (11/11/2026: "App compiled successfully")
- [x] 5.2 No comprovante (`impressao_state.py` e `pages/impressao.py`), mostrar a forma, a situação e a data do pagamento; verificar com `reflex compile --dry` (linha "Pagamento" nos dados da venda; `pages/impressao.py` já mostra as linhas do grupo e não precisou mudar)

## 6. Script, documentação e verificação

- [x] 6.1 Criar `scripts/testar_asaas.py` (confere a chave e o ambiente; cobrança de TESTE opcional, removida ao final); verificar rodando-o com a chave do Sandbox (11/11/2026: chave aceita; boleto TESTE criado e removido. A primeira remoção falhou com "erro desconhecido" do Asaas logo depois da criação, por isso `cancelar_cobranca` tenta de novo uma vez)
- [x] 6.2 Atualizar `README.md` (seção "Pagamentos pelo Asaas": configuração, Sandbox, teste), `docs/project-overview.md` (escopo, funcionalidades e arquitetura) e `docs/domain-model.md` (pagamento da venda); verificar lendo as seções
- [x] 6.3 Rodar `.venv\Scripts\python.exe -m unittest discover -s tests -t .` e `reflex compile --dry`; verificar que passam (11/11/2026: 100 testes OK, 30 deles novos; compilação OK)
- [ ] 6.4 Teste no app com dados TESTE (plano de migração do design, passo 4): boleto, cartão de teste, confirmação no painel do Sandbox, e-mail de confirmação e cancelamento; remover os registros TESTE ao final (11/11/2026: feito pelo serviço, com o Xano real e o Asaas Sandbox, usando um cliente TESTE sem e-mail. Os passos foram:
  - boleto gerado, com o link gravado na venda;
  - recebimento confirmado no Sandbox; a consulta passou a venda a PAGO, com a data;
  - venda com cartão cancelada, com a cobrança removida no Asaas e os dados do pagamento preservados;
  - cancelamento da venda paga, com o aviso de estorno;
  - registros TESTE removidos do Xano e do Sandbox.

  Falta com o grupo: conferir a tela no navegador e o e-mail real de confirmação, com um cliente TESTE que tenha o e-mail do grupo)
