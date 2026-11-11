## Context

Hoje `vendas_servico.registrar_venda` baixa o estoque, cria a venda em `transacoes`, grava os itens e devolve `(id, avisos)`. `cancelar_venda` marca a venda como cancelada e devolve o estoque, dentro de uma trava por venda (`_travas_venda`). A tabela `transacoes` não guarda nada sobre o pagamento. Os e-mails saem pelo SendGrid (`email_clientes.py`), em segundo plano. O servidor roda numa máquina Windows na rede da loja, **sem endereço público na internet**, e já executa uma tarefa periódica registrada com `app.register_lifespan_task` (`xano_client.manter_cache_aquecido`). O Xano está no plano gratuito, que limita as requisições, e o PATCH dele substitui o registro inteiro.

O Asaas oferece uma API REST (`https://api-sandbox.asaas.com/v3` no Sandbox), autenticada pelo cabeçalho `access_token`, com os recursos `customers` (clientes) e `payments` (cobranças). O próprio Asaas envia as cobranças ao cliente por e-mail e SMS quando as notificações do cliente estão ligadas.

## Goals / Non-Goals

**Goals:**
- Concluir a venda com a forma de pagamento e, quando for pelo Asaas, gerar a cobrança que o cliente recebe por e-mail e SMS.
- Saber quando a cobrança foi paga e enviar ao cliente o e-mail de confirmação da loja.
- Não perder vendas nem duplicar cobranças ou e-mails quando houver falhas de conexão.

**Non-Goals:**
- Produção do Asaas, parcelamento, estorno pelo sistema, webhook e mudanças no faturamento do Painel (ver a proposta).

## Decisions

### D1. Módulo `asaas_client.py`, no mesmo padrão do `xano_client.py`
Um módulo só fala com o Asaas, usando `httpx.AsyncClient` (já instalado), com tempo limite e mensagens de erro em português. As funções são:
- `buscar_cliente_por_cpf`, `criar_cliente`;
- `criar_cobranca`, `buscar_cobranca`, `buscar_cobranca_por_referencia`, `cancelar_cobranca` (DELETE `/payments/{id}`).

A configuração fica no `.env`, carregado pelo `_carregar_env` que já existe:
- `ASAAS_API_KEY`: a chave da conta Sandbox;
- `ASAAS_AMBIENTE`: só `sandbox` nesta change. Qualquer outro valor desliga a integração, com aviso no log;
- `ASAAS_INTERVALO_MINUTOS`: opcional, intervalo da consulta periódica (padrão 5).

`configurado()` diz se a integração está ligada. A chave nunca vai para o log, nem para a tela, nem para o Xano. Também é enviado um cabeçalho `User-Agent` fixo ("HarleyStore"), que o Asaas exige das contas novas. **Alternativa:** a biblioteca Python não oficial do Asaas. Foi descartada porque seria mais uma dependência, e as 6 chamadas são simples com `httpx`.

### D2. Regras em `pagamentos_servico.py`, com funções puras
As regras ficam fora do state, para serem testadas sem o Asaas:
- `FORMAS = {"NA_LOJA", "BOLETO", "CARTAO_CREDITO", "CLIENTE_ESCOLHE"}`, com o tipo do Asaas de cada forma: `BOLETO`, `CREDIT_CARD` e `UNDEFINED`;
- `problema_cliente(cliente)`: confere o CPF/CNPJ com `validacao.py` e exige e-mail ou celular;
- `dados_cliente_asaas(cliente)`: monta nome, CPF/CNPJ só com números, e-mail e telefone, com `notificationDisabled = false`. O celular (11 dígitos com 9 depois do DDD) vai em `mobilePhone`; outro número vai em `phone`;
- `dados_cobranca(venda, cliente_asaas_id, forma, vencimento)`: monta valor, `dueDate` no formato AAAA-MM-DD, descrição "Venda nº X - Harley Store" e `externalReference = "venda-<id>"`;
- `situacao_pelo_asaas(cobranca)`: traduz o status do Asaas para a situação da venda:
  - RECEIVED, CONFIRMED ou RECEIVED_IN_CASH → PAGO;
  - OVERDUE → VENCIDO;
  - cobrança com `deleted` → COBRANCA_CANCELADA;
  - PENDING e os demais → AGUARDANDO.
- `vencimento_valido(data, hoje)` e `vencimento_padrao(hoje)`, que soma 3 dias.

### D3. Campos novos em `transacoes` (dependem da aprovação do grupo)
São todos opcionais:
- `text forma_pagamento`: NA_LOJA, BOLETO, CARTAO_CREDITO ou CLIENTE_ESCOLHE;
- `text situacao_pagamento`: NA_LOJA, SEM_COBRANCA, AGUARDANDO, PAGO, VENCIDO ou COBRANCA_CANCELADA;
- `text asaas_cobranca_id`;
- `text link_cobranca`, a `invoiceUrl` do Asaas;
- `timestamp data_pagamento`.

Vazio significa venda antiga, mostrada como "Não informado". **Alternativa:** uma tabela `pagamentos` separada. Foi descartada porque toda venda tem no máximo uma cobrança, e uma tabela nova custaria mais requisições ao Xano Free. Nenhum campo novo em `clientes`: o cliente é encontrado no Asaas pelo CPF/CNPJ (`GET /customers?cpfCnpj=`), e isso custa uma chamada ao Asaas, não ao Xano.

**Atenção ao PATCH:** como o PATCH do Xano substitui o registro inteiro, os pontos que já atualizam `transacoes` passam a enviar também os 5 campos novos. São eles `_marcar_cancelada` e a ligação com `id_moto_cliente` em `vendas_servico.py`. Sem isso, cancelar uma venda apagaria os dados do pagamento. Haverá teste para esse caso. Como na change `venda-de-motos-no-balcao`, o servidor confere se o Xano já tem os campos antes de aceitar uma forma pelo Asaas. Se não tiver, recusa com o pedido de rodar `scripts/aplicar_xano.ps1`.

### D4. Ordem das operações no registro
1. Validar o tipo, os itens, a forma, o vencimento e, nas formas pelo Asaas, o cliente (`problema_cliente`). Isso acontece **antes** de baixar o estoque, e uma recusa não altera nada.
2. Registrar a venda como hoje (estoque, venda, itens, moto), já com `forma_pagamento` e com a situação `NA_LOJA`, ou `SEM_COBRANCA` nas formas pelo Asaas.
3. Nas formas pelo Asaas, chamar `gerar_cobranca(venda_id)`:
   - procurar a cobrança pela referência `venda-<id>` e reaproveitá-la se existir;
   - se não existir, procurar ou criar o cliente no Asaas e criar a cobrança;
   - atualizar a venda com o id, o link e a situação AGUARDANDO.

Uma falha no passo 3 **não desfaz a venda**: a venda fica em SEM_COBRANCA ("Falha na cobrança") e o funcionário recebe um aviso. **Motivo:** a mercadoria já saiu do estoque, e desfazer tudo por uma queda do Asaas seria pior do que tentar a cobrança de novo. A mesma função `gerar_cobranca` atende o botão "Gerar cobrança de novo", e a busca pela referência evita cobrança duplicada quando a resposta do Asaas se perde. **Alternativa:** criar a cobrança antes da venda. Foi descartada porque deixaria cobranças no Asaas para vendas recusadas por falta de estoque.

### D5. Confirmação por consulta periódica, e não por webhook
O servidor fica na rede da loja, sem endereço público, e por isso o Asaas não conseguiria chamar um webhook. Uma tarefa registrada com `app.register_lifespan_task` roda a cada `ASAAS_INTERVALO_MINUTOS` e faz o seguinte:
- lê as vendas pelo cache do `xano_client.listar`, sem requisição extra ao Xano quando o cache está quente;
- filtra as vendas não canceladas em AGUARDANDO ou VENCIDO;
- consulta cada cobrança no Asaas;
- só grava no Xano quando a situação muda.

Assim a consulta quase não gasta requisições do Xano. O botão "Atualizar pagamentos" roda a mesma função na hora. Cada venda é tratada dentro da trava `_travas_venda` de `vendas_servico.py`, a mesma do cancelamento, para que a consulta e um cancelamento simultâneo não se sobreponham. **Alternativa:** um túnel (ngrok ou similar) para receber o webhook. Foi descartada porque expõe o servidor da loja à internet e depende de mais um serviço.

### D6. E-mail de confirmação enviado uma única vez
Na passagem para PAGO, o servidor **primeiro** grava a venda como PAGO, com `data_pagamento` (`paymentDate` ou `clientPaymentDate` do Asaas). Só depois de gravar com sucesso ele chama `email_clientes.pagamento_confirmado(nome, email, venda_id, valor, forma, data)`. Se a gravação falhar, o e-mail não sai, e a próxima consulta tenta de novo. Como só a passagem de AGUARDANDO ou VENCIDO para PAGO envia o e-mail, uma consulta repetida não reenvia. O modelo do e-mail é o `_modelo_html` que já existe.

### D7. Cancelamento
Em `cancelar_venda`, depois de marcar a venda como cancelada e devolver o estoque (ordem atual), o servidor trata a cobrança da venda:
- se a venda estiver em AGUARDANDO ou VENCIDO, chama `cancelar_cobranca` e grava COBRANCA_CANCELADA. Se essa chamada falhar, a venda continua cancelada e o funcionário recebe um aviso;
- se a venda estiver PAGO, o pagamento não muda, e o sistema avisa que o estorno é feito no painel do Asaas.

As mensagens entram em `_juntar`, junto com os avisos de moto que já existem.

### D8. Tela de Vendas / Balcão e comprovante
No formulário de registro entram:
- o seletor "Forma de pagamento", que só tem "Na loja" quando o Asaas não está configurado;
- o campo "Vencimento", visível nas formas pelo Asaas.

Na lista de vendas entram:
- o selo da situação do pagamento, nas cores do tema;
- o link "Abrir cobrança";
- o botão "Gerar cobrança de novo", nas vendas em SEM_COBRANCA;
- o botão "Atualizar pagamentos".

Tudo isso é feito em Reflex, no par `vendas_state.py` e `pages/vendas.py`. Não há state novo: o `VendasState` já está no `ExigeSessaoMiddleware`. O comprovante (`impressao_state.py` e `pages/impressao.py`) ganha a linha "Pagamento: <forma> - <situação>", com a data quando o pagamento estiver PAGO.

### D9. Script de conferência
O script `scripts/testar_asaas.py`, no mesmo estilo do `testar_sendgrid.py`, faz o seguinte:
- confere a chave e o ambiente, consultando a conta (`GET /myAccount` ou `/finance/balance`);
- lista quantas cobranças estão aguardando;
- opcionalmente, cria um cliente e uma cobrança de TESTE de R$ 5,00 e os remove ao final.

## Risks / Trade-offs

- [O Xano ainda não tem os campos novos] → as formas pelo Asaas são recusadas com o aviso de qual script rodar; as vendas "Na loja" seguem normais.
- [O PATCH sem os campos novos apagaria o pagamento] → todos os pontos que atualizam `transacoes` passam a enviar os 5 campos, com teste automático do cancelamento.
- [Confirmação com até alguns minutos de atraso] → é aceitável para boleto, que leva de 1 a 3 dias úteis para compensar; o botão "Atualizar pagamentos" adianta a consulta.
- [Servidor desligado por dias] → na volta, a primeira consulta encontra as cobranças pagas e envia os e-mails atrasados, um por venda.
- [O Sandbox do Asaas pode não enviar SMS de verdade] → o grupo confere no Sandbox o que chega por e-mail e por SMS. O comportamento do Sandbox não muda o sistema.
- [A trava por venda vale só dentro de um processo] → é a mesma limitação das travas atuais; a loja roda um único processo.
- [A chave do Asaas vazar] → ela fica só no `.env`, que está fora do git; a chave do Sandbox não movimenta dinheiro real.

## Migration Plan

1. O grupo cria a conta no Asaas Sandbox e gera a chave de API. Depois coloca no `.env` de cada pasta (desenvolvimento e produção) as linhas `ASAAS_API_KEY=...` e `ASAAS_AMBIENTE=sandbox`.
2. O grupo roda `.\scripts\aplicar_xano.ps1`, confere a prévia (5 campos em `transacoes` e os endpoints) e confirma.
3. Publicar o código e rodar `scripts\testar_asaas.py`.
4. Teste com dados TESTE:
   - um cliente TESTE com e-mail e celular do grupo faz uma venda com boleto;
   - conferir o e-mail e o SMS do Asaas;
   - no painel do Sandbox, confirmar o pagamento ("Confirmar recebimento");
   - conferir a venda como "Pago" e o e-mail de confirmação;
   - repetir com cartão (cartão de teste do Asaas) e cancelar uma venda com boleto em aberto.

   Ao final, cancelar as vendas e remover o cliente TESTE.

**Para desfazer:** reverter o commit e retirar `ASAAS_API_KEY` do `.env`. Os campos novos podem ficar no Xano, porque são opcionais.

## Decisões do grupo (11/11/2026)

O grupo aprovou a change com as sugestões da proposta:
- os 5 campos novos em `transacoes` (D3);
- vencimento padrão de 3 dias;
- cancelar uma venda já paga é **permitido**, com o aviso de fazer o estorno no painel do Asaas;
- o faturamento do Painel não muda: a venda conta no dia em que é registrada.

## Notas da implementação

- O vencimento escolhido na tela não é gravado na venda. Por isso "Gerar cobrança de novo" usa o vencimento padrão, de 3 dias contados a partir do dia da nova tentativa.
- No cancelamento, a cobrança é tratada logo depois de a venda ser marcada como cancelada, e não depois da devolução do estoque. Assim o aviso também aparece nas vendas sem itens gravados. Continua valendo que nada disso impede o cancelamento.
- Nos primeiros segundos depois de criado, o boleto é recusado pelo Sandbox com "erro desconhecido", tanto ao remover quanto ao confirmar o recebimento. No teste, ele foi liberado em cerca de 10 segundos; o cartão não tem essa espera. Por isso `cancelar_cobranca` tenta de novo até 3 vezes, com 5 segundos de espera entre as tentativas.
- A conferência da chave usa `GET /finance/balance` (saldo da conta).
