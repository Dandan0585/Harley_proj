## ADDED Requirements

### Requirement: Forma de pagamento na conclusão da venda
Ao registrar uma venda, o sistema SHALL oferecer as formas de pagamento "Na loja", "Boleto", "Cartão de crédito" e "Cliente escolhe", com "Na loja" como padrão. O servidor MUST recusar uma forma fora dessa lista. Nas formas pelo Asaas (todas, exceto "Na loja"), o funcionário SHALL informar a data de vencimento, inicialmente 3 dias depois da venda. O servidor MUST recusar um vencimento anterior à data da venda. A forma "Na loja" MUST NOT gerar cobrança no Asaas.

#### Scenario: Venda paga na loja
- **WHEN** o funcionário registra uma venda com a forma "Na loja"
- **THEN** a venda é registrada como hoje, com a situação de pagamento "Na loja", e nada é enviado ao Asaas

#### Scenario: Venda com boleto
- **WHEN** o funcionário registra uma venda de R$ 213,00 com a forma "Boleto" e vencimento em 3 dias, para um cliente com CPF e e-mail
- **THEN** a venda é registrada, uma cobrança por boleto de R$ 213,00 com esse vencimento é criada no Asaas e a venda fica "Aguardando pagamento"

#### Scenario: Forma inválida enviada ao servidor
- **WHEN** chega ao servidor um pedido de venda com a forma de pagamento "CHEQUE"
- **THEN** a venda não é registrada, nenhum estoque é alterado e o funcionário é informado de que a forma não é válida

#### Scenario: Vencimento no passado
- **WHEN** o funcionário escolhe "Boleto" com vencimento anterior à data de hoje
- **THEN** a venda não é registrada e o sistema pede outra data de vencimento

### Requirement: Cliente exigido para cobrança no Asaas
Uma venda com forma de pagamento pelo Asaas MUST ter um cliente com CPF/CNPJ válido e com e-mail ou celular. O servidor MUST conferir isso antes de baixar o estoque e, faltando algum dado, MUST recusar a venda informando o que falta.

#### Scenario: Venda com boleto sem cliente
- **WHEN** o funcionário tenta registrar uma venda com a forma "Boleto" sem escolher um cliente
- **THEN** a venda não é registrada, nenhum estoque é alterado e o sistema pede o cliente

#### Scenario: Cliente sem e-mail e sem celular
- **WHEN** o funcionário escolhe "Cartão de crédito" para um cliente sem e-mail e sem celular
- **THEN** a venda não é registrada e o sistema pede para completar o cadastro do cliente

### Requirement: Cliente registrado no Asaas
Antes de criar a cobrança, o sistema SHALL procurar o cliente no Asaas pelo CPF/CNPJ. Se ele não existir, o sistema SHALL criá-lo com nome, CPF/CNPJ, e-mail e celular, com as notificações de cobrança por e-mail e SMS ligadas. O sistema MUST NOT criar dois cadastros no Asaas para o mesmo CPF/CNPJ.

#### Scenario: Primeiro pagamento do cliente pelo Asaas
- **WHEN** uma venda com boleto é registrada para um cliente que ainda não existe no Asaas
- **THEN** o cliente é criado no Asaas com o nome, o CPF/CNPJ, o e-mail e o celular do cadastro da loja

#### Scenario: Cliente já cadastrado no Asaas
- **WHEN** uma segunda venda com boleto é registrada para o mesmo cliente
- **THEN** a cobrança usa o cadastro existente no Asaas e nenhum cliente novo é criado lá

### Requirement: Cobrança da venda no Asaas
Depois de registrar a venda, o sistema SHALL criar no Asaas uma cobrança com o total da venda, a forma de pagamento, o vencimento, uma descrição com o número da venda e o número da venda como referência externa. O tipo da cobrança MUST ser boleto para "Boleto", cartão de crédito para "Cartão de crédito" e escolha do cliente para "Cliente escolhe". A venda SHALL guardar o identificador da cobrança, o link de pagamento e a situação "Aguardando pagamento". Os dados do cartão MUST ser digitados apenas na página de pagamento do Asaas e MUST NOT passar pelo sistema da loja.

#### Scenario: Link de pagamento na lista de vendas
- **WHEN** uma venda com cobrança no Asaas é registrada
- **THEN** a lista de vendas mostra a venda como "Aguardando pagamento", com o link da cobrança

#### Scenario: Cobrança com cartão
- **WHEN** uma venda é registrada com a forma "Cartão de crédito"
- **THEN** o cliente recebe do Asaas o link da cobrança e digita os dados do cartão na página do Asaas

### Requirement: Falha ao gerar a cobrança
Se a cobrança não puder ser criada no Asaas (falha de conexão ou recusa do Asaas), a venda MUST continuar registrada, com a situação "Falha na cobrança", e o funcionário MUST ser avisado com o motivo. O sistema SHALL oferecer a ação "Gerar cobrança de novo" para essas vendas. Uma nova tentativa MUST NOT criar uma segunda cobrança para a mesma venda: antes de criar, o sistema procura no Asaas uma cobrança com a referência da venda.

#### Scenario: Asaas fora do ar
- **WHEN** uma venda com boleto é registrada e o Asaas não responde
- **THEN** a venda fica registrada como "Falha na cobrança", o estoque continua baixado e o funcionário é avisado para gerar a cobrança de novo

#### Scenario: Nova tentativa depois de uma resposta perdida
- **WHEN** a cobrança foi criada no Asaas, a resposta se perdeu, e o funcionário aciona "Gerar cobrança de novo"
- **THEN** o sistema encontra a cobrança existente pela referência da venda, liga-a à venda e não cria outra

### Requirement: Confirmação do pagamento
O servidor SHALL consultar no Asaas, periodicamente e também quando o funcionário acionar "Atualizar pagamentos", a situação das cobranças das vendas que aguardam pagamento. Quando o Asaas informar que a cobrança foi recebida ou confirmada, a venda MUST passar a "Pago", com a data do pagamento. Quando o Asaas informar que a cobrança venceu, a venda MUST passar a "Vencido" e continuar sendo consultada. Quando o Asaas informar que a cobrança foi removida, a venda MUST passar a "Cobrança cancelada". A situação MUST mudar uma única vez para cada mudança no Asaas.

#### Scenario: Boleto pago
- **WHEN** o cliente paga o boleto de uma venda e o Asaas confirma o pagamento
- **THEN** na próxima consulta a venda passa a "Pago", com a data do pagamento

#### Scenario: Boleto vencido e pago depois
- **WHEN** um boleto vence sem pagamento e é pago dias depois
- **THEN** a venda passa primeiro a "Vencido" e depois a "Pago"

#### Scenario: Consulta sem mudanças
- **WHEN** a consulta periódica encontra todas as cobranças na mesma situação
- **THEN** nenhuma venda é alterada no banco

### Requirement: Asaas não configurado
Sem a chave de API do Asaas configurada no servidor, o sistema MUST oferecer apenas a forma "Na loja", MUST recusar no servidor as formas pelo Asaas e MUST continuar registrando vendas normalmente. A chave MUST ficar só no servidor, fora do git, e MUST NOT aparecer na tela nem no log.

#### Scenario: Servidor sem a chave do Asaas
- **WHEN** o funcionário abre a tela de vendas e a chave do Asaas não está configurada
- **THEN** a forma de pagamento oferece só "Na loja" e a venda é registrada normalmente

### Requirement: Vendas antigas sem forma de pagamento
Vendas registradas antes desta versão, sem forma de pagamento gravada, MUST ser exibidas com a situação "Não informado" e MUST NOT ser consultadas no Asaas.

#### Scenario: Consultar uma venda antiga
- **WHEN** alguém consulta uma venda registrada antes desta versão
- **THEN** a venda aparece com a forma de pagamento "Não informado" e sem link de cobrança
