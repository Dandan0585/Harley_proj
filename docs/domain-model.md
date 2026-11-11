# Domain Model — Harley Store

Este documento descreve os conceitos do negócio e como eles se relacionam.
Ele não é o modelo físico do banco: o esquema real das tabelas está em
`xano/table/`.

## Visão geral

```text
Cliente
 ├── Moto do cliente
 │     └── Ordem de serviço ── Funcionário (mecânico)
 │           └── Item da OS ── (Produto | Mão de obra)
 ├── Venda ── Funcionário (vendedor)
 │     └── Item da venda ── (Produto | Mão de obra | Moto da loja)
 └── Moto da loja (quando compra uma)

Fornecedor
 └── Compra
       └── Item da compra ── Produto

Produto
 └── Movimentação de estoque (origem: venda, OS, compra, ajuste…)

Usuário (conta de acesso: Administrador | Funcionário)
```

## Cliente

Pessoa ou empresa atendida pela loja.

- **Principais informações:** nome, CPF/CNPJ, telefone, e-mail, endereço.
- **Relacionamentos:** pode ter várias motos, várias vendas e ser
  comprador de motos da loja.
- **Regras:** CPF/CNPJ válido e único; não pode ser excluído se tiver motos
  ou vendas. Ao ser cadastrado com e-mail, recebe e-mail de boas-vindas.

## Moto do cliente

Moto que pertence a um cliente e é atendida pela oficina.

- **Principais informações:** modelo, placa, chassi, foto.
- **Relacionamentos:** pertence a um cliente; pode ter várias ordens de
  serviço.
- **Regras:** placa e chassi válidos e únicos; sem foto própria, mostra a
  foto oficial do modelo.

## Moto da loja

Moto que a loja tem para vender (estoque de motos).

- **Principais informações:** marca, modelo, ano, cor, placa, chassi,
  quilometragem, RENAVAM, cilindrada, situação, preço de compra e de
  venda, datas de entrada e saída, fotos.
- **Relacionamentos:** quando vendida, fica ligada ao cliente comprador.
- **Regras:** só a situação "Vendida" tira a moto do estoque, e exige
  cliente e chassi. O valor do estoque de motos usa o preço de compra.
  Pode ser vendida pelo próprio cadastro ou no Balcão, como item de uma
  venda (uma por venda, pelo preço de venda); nesse caso passa a constar
  nas motos do cliente comprador, e o cancelamento da venda a devolve ao
  estoque. A venda gera e-mail de parabéns ao cliente.

## Produto

Item vendido no balcão ou usado na oficina (peças, acessórios, vestuário,
lubrificantes etc.).

- **Principais informações:** nome, descrição, categoria, quantidade em
  estoque, preço de venda, foto.
- **Relacionamentos:** aparece em itens de venda, de OS e de compra; tem um
  histórico de movimentações de estoque.
- **Regras:** estoque nunca negativo; estoque baixo a partir de 5
  unidades; categoria livre (nova categoria é só digitada).

## Venda (transação)

Registro de uma venda no balcão.

- **Principais informações:** tipo, data, funcionário, cliente (opcional),
  valor total, situação, forma de pagamento e situação do pagamento.
- **Relacionamentos:** tem um ou mais itens; cada item é um produto do
  estoque, um serviço avulso (mão de obra) ou uma moto da loja.
- **Regras:** baixa o estoque na hora; nunca é apagada, só cancelada (com
  motivo opcional), o que devolve os produtos e tira a venda do
  faturamento.

## Pagamento da venda

Como o cliente paga a venda. Fica na própria venda (não é tabela à parte).

- **Principais informações:** forma (Na loja, Boleto, Cartão de crédito,
  Cliente escolhe), situação (Na loja, Aguardando pagamento, Pago, Vencido,
  Cobrança cancelada, Falha na cobrança), cobrança e link no Asaas, data do
  pagamento.
- **Relacionamentos:** pertence a uma venda; a cobrança fica no Asaas, em
  nome do cliente da venda (encontrado lá pelo CPF/CNPJ).
- **Regras:** cobrar pelo Asaas exige cliente com CPF/CNPJ válido e e-mail
  ou celular; uma falha ao gerar a cobrança não desfaz a venda e pode ser
  repetida sem cobrar duas vezes; quando o Asaas confirma o pagamento, o
  cliente recebe um único e-mail de confirmação; cancelar a venda cancela a
  cobrança em aberto (venda já paga: estorno no painel do Asaas). A venda
  conta no faturamento no dia do registro, paga ou não. Vendas antigas
  aparecem com o pagamento "Não informado".

## Ordem de serviço (OS)

Atendimento da oficina a uma moto de cliente.

- **Principais informações:** moto, mecânico, data de abertura, situação
  (Aberta, Em andamento, Concluída, Cancelada), data de conclusão.
- **Relacionamentos:** tem itens: peças (produtos, que baixam o estoque) e
  mão de obra (descrição e valor).
- **Regras:** ao ser concluída, peças + mão de obra entram no faturamento
  do dia da conclusão; excluir a OS devolve as peças ao estoque.

## Fornecedor e Compra

**Fornecedor:** empresa que vende mercadorias à loja (nome, CNPJ, contato).

**Compra (entrada de mercadoria):** pedido recebido de um fornecedor, com
data, valor total, descrição e um ou mais itens (produto, quantidade, valor
unitário).

- **Regras:** cada item soma no estoque; excluir a compra retira o que ela
  somou e é recusado se esses produtos já foram vendidos. Compras não
  entram no faturamento.

## Movimentação de estoque

Registro de cada alteração no saldo de um produto.

- **Principais informações:** produto, quantidade (+/−), saldo após,
  origem (venda, cancelamento, OS, compra, edição), referência e usuário.
- **Regras:** toda mudança de saldo gera uma movimentação; é a base do
  histórico de estoque.

## Funcionário

Pessoa que trabalha na loja.

- **Principais informações:** nome, cargo, tipo (Vendedor, Mecânico,
  Gerente), contato.
- **Relacionamentos:** registra vendas; é o responsável pelas ordens de
  serviço.

## Usuário (conta de acesso)

Conta usada para entrar no sistema.

- **Principais informações:** nome, e-mail, senha, perfil
  (Administrador ou Funcionário).
- **Regras:** só administradores criam e gerenciam contas; ninguém altera
  o próprio perfil nem exclui a própria conta. A conta nova recebe um
  e-mail de boas-vindas, sem a senha. Existe uma conta de serviço usada
  pelo servidor do sistema para acessar os dados.
- **Diferença para Funcionário:** o funcionário é o cadastro de RH (sem
  login e sem e-mail); quem usa o sistema precisa de uma conta de usuário.

## Conceitos derivados (calculados, não armazenados)

- **Faturamento:** vendas não canceladas (produtos + mão de obra) + OS
  concluídas, separado entre motos e produtos, por dia e por mês.
- **Valor do estoque:** motos pelo preço de compra; produtos por
  quantidade × preço de venda.
