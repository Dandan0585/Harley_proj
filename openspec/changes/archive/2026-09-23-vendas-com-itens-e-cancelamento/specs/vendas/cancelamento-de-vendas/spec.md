# Spec Delta

## Purpose

Permite desfazer vendas sem perder o histórico: a venda cancelada continua registrada e marcada como tal, deixa de contar no faturamento e devolve os produtos ao estoque, inclusive cancelando várias vendas de uma vez.

## ADDED Requirements

### Requirement: Cancelamento preserva o histórico
Cancelar uma venda MUST NOT apagá-la. A venda SHALL passar à situação "Cancelada", registrando a data e hora do cancelamento e, opcionalmente, um motivo informado pelo funcionário. Vendas canceladas MUST continuar visíveis na lista de vendas, identificadas como canceladas. O sistema MUST NOT oferecer a exclusão de vendas.

#### Scenario: Cancelar uma venda
- **WHEN** o funcionário cancela uma venda ativa, informando o motivo "Cliente desistiu"
- **THEN** a venda continua na lista, com a situação "Cancelada", a data do cancelamento e o motivo

#### Scenario: Cancelamento exige confirmação
- **WHEN** o funcionário aciona o cancelamento
- **THEN** o sistema pede confirmação antes de cancelar, e nada muda se ele desistir

### Requirement: Devolução do estoque no cancelamento
Ao cancelar uma venda, o sistema MUST devolver ao estoque a quantidade de cada item que for produto. Itens avulsos MUST NOT alterar o estoque. A devolução MUST seguir a mesma proteção contra operações simultâneas das vendas.

#### Scenario: Estoque devolvido
- **WHEN** é cancelada uma venda que baixou 2 unidades de um produto cujo estoque atual é 8
- **THEN** o estoque desse produto passa a ser 10

#### Scenario: Venda antiga sem itens
- **WHEN** é cancelada uma venda registrada antes desta versão, sem itens gravados
- **THEN** a venda é marcada como cancelada, nenhum estoque é alterado e o sistema avisa que o estoque dessa venda precisa ser conferido manualmente

### Requirement: Cancelamento único
Uma venda já cancelada MUST NOT poder ser cancelada de novo, e o estoque de uma venda MUST ser devolvido no máximo uma vez, mesmo que dois funcionários tentem cancelá-la ao mesmo tempo.

#### Scenario: Tentar cancelar venda já cancelada
- **WHEN** uma venda já está cancelada
- **THEN** a opção de cancelar não é oferecida para ela

#### Scenario: Cancelamento simultâneo da mesma venda
- **WHEN** dois funcionários confirmam, ao mesmo tempo, o cancelamento da mesma venda
- **THEN** a venda é cancelada uma única vez e o estoque é devolvido uma única vez

### Requirement: Cancelar várias vendas de uma vez
O sistema SHALL permitir selecionar várias vendas ativas na lista e cancelá-las com uma única confirmação, com o mesmo motivo opcional. Ao final, o sistema MUST informar quantas vendas foram canceladas e quais não puderam ser canceladas, e por quê.

#### Scenario: Cancelamento em lote
- **WHEN** o funcionário seleciona 3 vendas ativas e confirma o cancelamento em lote
- **THEN** as 3 vendas ficam canceladas, o estoque de todas é devolvido e o sistema informa "3 vendas canceladas"

#### Scenario: Lote com venda que falha
- **WHEN** em um lote de 3 vendas, uma não pode ser cancelada (por exemplo, falha de conexão)
- **THEN** as outras 2 são canceladas normalmente, e o sistema informa qual venda não foi cancelada, para que se tente de novo

#### Scenario: Vendas canceladas não são selecionáveis
- **WHEN** a lista mostra vendas ativas e canceladas
- **THEN** apenas as vendas ativas podem ser selecionadas para cancelamento

### Requirement: Vendas canceladas fora do faturamento
Vendas canceladas MUST NOT ser somadas no faturamento do dia, no faturamento do mês nem no gráfico de faturamento do painel. Na atividade recente do painel, elas MUST aparecer identificadas como canceladas.

#### Scenario: Faturamento após cancelamento
- **WHEN** o faturamento do dia é R$ 500,00 e uma venda de R$ 200,00 feita hoje é cancelada
- **THEN** o faturamento do dia passa a ser R$ 300,00

### Requirement: Comprovante de venda cancelada
O comprovante impresso de uma venda cancelada MUST indicar de forma destacada que a venda está cancelada, com a data e o motivo do cancelamento.

#### Scenario: Imprimir venda cancelada
- **WHEN** alguém imprime o comprovante de uma venda cancelada
- **THEN** o documento mostra "VENDA CANCELADA", a data do cancelamento e o motivo, além dos itens e do total original
