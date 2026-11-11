## Why

Hoje a venda no Balcão termina quando é registrada, e o sistema não guarda como o cliente vai pagar. O grupo quer concluir o pedido com a forma de pagamento: boleto ou cartão, escolhida pelo cliente. A cobrança deve ser enviada ao cliente por e-mail e SMS, e a loja deve saber quando o pagamento foi feito. Para isso será usada a plataforma de pagamentos **Asaas**, primeiro no ambiente **Sandbox**, onde nenhum dinheiro de verdade é movimentado. Quando o pagamento for confirmado, o cliente deve receber um e-mail da loja com a confirmação.

## What Changes

- **Forma de pagamento na conclusão da venda.** Ao registrar a venda, o funcionário escolhe uma forma de pagamento:
  - **Na loja**: dinheiro ou maquininha, sem cobrança no Asaas. É a opção padrão e funciona como hoje;
  - **Boleto**;
  - **Cartão de crédito**;
  - **Cliente escolhe**: o link de pagamento oferece boleto, cartão ou Pix, e o cliente decide.

  Nas três últimas opções, o funcionário também informa a data de vencimento (padrão: 3 dias depois da venda).
- **Cliente registrado no Asaas.** Quando a cobrança é pelo Asaas, a venda exige um cliente com CPF/CNPJ válido e com e-mail ou celular. O servidor procura o cliente no Asaas pelo CPF/CNPJ e, se ele ainda não existir, cria o cadastro com nome, CPF/CNPJ, e-mail e celular, com as notificações por e-mail e SMS ligadas.
- **Cobrança gerada no Asaas.** Depois que a venda é registrada, o servidor cria a cobrança no Asaas, com o total da venda, a forma de pagamento, o vencimento e a referência da venda. O próprio Asaas envia a cobrança ao cliente por e-mail e SMS, com o link de pagamento. Os dados do cartão são digitados pelo cliente na página do Asaas e **nunca passam pelo sistema da loja**.
- **Situação do pagamento** em cada venda: Na loja, Aguardando pagamento, Pago, Vencido, Cobrança cancelada ou Falha na cobrança. A situação aparece na lista de vendas, junto com o link da cobrança. Se a cobrança falhar, por exemplo por queda de conexão, a venda continua registrada e a tela oferece o botão **Gerar cobrança de novo**.
- **Confirmação do pagamento.** O servidor consulta no Asaas, periodicamente, as cobranças que aguardam pagamento. Quando o Asaas informa que uma cobrança foi paga, a venda passa a **Pago**, com a data do pagamento, e o cliente recebe pelo SendGrid um **e-mail de confirmação de pagamento** com a identidade visual da loja. A tela de vendas também tem o botão **Atualizar pagamentos**.
- **Cancelamento.** Ao cancelar uma venda com cobrança aguardando pagamento, o sistema também cancela a cobrança no Asaas. Se a cobrança já tiver sido paga, a venda é cancelada normalmente e o sistema avisa que o estorno deve ser feito no painel do Asaas.
- **Comprovante de venda** passa a mostrar a forma e a situação do pagamento.
- **Configuração** no `.env`: chave de API do Asaas e o ambiente (sandbox). Sem a chave, só a opção "Na loja" fica disponível, e o app continua funcionando como hoje.
- **Banco (Xano), depende da aprovação do grupo:** campos opcionais novos em `transacoes`: `forma_pagamento`, `situacao_pagamento`, `asaas_cobranca_id`, `link_cobranca` e `data_pagamento`. Os endpoints POST, PUT e PATCH de `transacoes` passam a gravá-los. O grupo aplica a mudança com `scripts/aplicar_xano.ps1`. Nenhum campo novo em `clientes`, porque o cliente é encontrado no Asaas pelo CPF/CNPJ.
- **Documentação:** `README.md` (nova seção sobre o Asaas), `docs/project-overview.md` (pagamentos online saem de "Fora do escopo"; nova integração na arquitetura) e `docs/domain-model.md` (pagamento da venda).

**Fora do escopo:**
- ambiente de produção do Asaas, com dinheiro real. A troca de ambiente fica preparada pela configuração, mas só será feita em outra change;
- parcelamento no cartão, desconto, juros e multa por atraso;
- Pix como opção separada (o Pix só aparece no link quando o cliente escolhe a forma);
- estorno pelo sistema (é feito no painel do Asaas);
- cobrança de ordens de serviço e de compras de fornecedores;
- mudar o faturamento do Painel: a venda continua contando no dia em que é registrada, esteja paga ou não;
- recebimento de avisos do Asaas (webhook), porque o servidor fica na rede da loja e não tem endereço público na internet;
- os e-mails e SMS de cobrança enviados pelo próprio Asaas, cujo texto é definido no painel do Asaas, e não no sistema;
- campos novos na tabela `clientes`.

## Capabilities

### New Capabilities

- `vendas/pagamento-da-venda`: forma de pagamento na conclusão da venda, cadastro do cliente e cobrança no Asaas, situação do pagamento, nova tentativa de cobrança e confirmação do pagamento.

### Modified Capabilities

- `vendas/cancelamento-de-vendas`: o cancelamento também cancela a cobrança aberta no Asaas e avisa quando a venda já foi paga.
- `clientes/emails-aos-clientes`: novo e-mail de confirmação de pagamento.
- `documentos/impressao`: o comprovante de venda traz a forma e a situação do pagamento.

## Impact

- Código novo: `harley_store/asaas_client.py` (acesso à API do Asaas, no mesmo padrão do `xano_client.py`) e `harley_store/pagamentos_servico.py` (regras do pagamento, com funções puras testáveis).
- Código alterado: `harley_store/vendas_servico.py` (registro e cancelamento), `harley_store/state/vendas_state.py` e `harley_store/pages/vendas.py` (forma de pagamento, situação, botões), `harley_store/email_clientes.py` (e-mail de confirmação), `harley_store/state/impressao_state.py` e `harley_store/pages/impressao.py` (comprovante), `harley_store/harley_store.py` (tarefa de consulta periódica).
- Xano: espelho em `xano/table/transacoes.xs` e nos endpoints de `xano/api/harley/transacoes*`. O grupo aplica com `scripts/aplicar_xano.ps1`.
- Serviço externo: Asaas Sandbox (`https://api-sandbox.asaas.com/v3`). Nenhuma biblioteca nova: o projeto já usa `httpx`.
- Testes: `tests/test_pagamentos.py`, com o Asaas e o Xano simulados.
