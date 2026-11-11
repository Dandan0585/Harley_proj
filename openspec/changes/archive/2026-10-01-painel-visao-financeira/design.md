## Context

Motivação em proposal.md. O banco é o Xano, acessado por API REST: não há SQL nem `SUM/GROUP BY` no banco, e as tabelas chegam como listas. Vender uma moto da loja não cria registro em `transacoes`: a venda fica na própria moto (situação Vendida, data de saída e cliente). A tabela `produtos` não tem preço de custo nem campo "ativo". Não há campo de desconto: o desconto é dado no preço unitário de cada item. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Números iguais a um cálculo independente sobre os mesmos dados.
- Nenhuma mudança visual além dos cards pedidos.

**Non-Goals:**
- Alterar o banco (nenhum campo novo).
- Incluir as ordens de serviço (decidido nesta data; incluído depois em `mao-de-obra-no-faturamento`).

## Decisions

### D1. Cálculo no servidor, em funções puras
`dashboard_state.py` tem `valor_estoque_motos`, `valor_estoque_produtos`, `lancamentos_faturamento` e `resumo_faturamento`, sem acesso ao Xano, testadas em `tests/test_painel.py`. O `DashboardState.carregar` só busca as tabelas e chama essas funções.

### D2. Decimal até o fim
Os valores vêm do Xano como número e são convertidos para `Decimal(str(valor))`; só a série do gráfico vira `float`, no último passo.

### D3. Fuso explícito
As datas do Xano (epoch em milissegundos, UTC) são convertidas com `ZoneInfo("America/Sao_Paulo")`, do pacote `tzdata`; sem o pacote, usa UTC-3 fixo (o Brasil não tem horário de verão desde 2019).

### D4. Regras aprovadas pelo dono da loja
As regras de cada card (situações das motos, base de preço, tipos de venda excluídos, classificação das vendas antigas) foram apresentadas antes da implementação e aprovadas em 01/10/2026.

## Risks / Trade-offs

- [Valor da moto vendida é o preço de venda gravado] → Se a negociação for por outro valor, o preço precisa ser atualizado antes de marcar Vendida.
- [Moto sem preço de compra conta como R$ 0,00] → Informado ao dono da loja; o card fica abaixo do real até os preços serem preenchidos.
- [Horários das vendas importadas 3 horas adiantados] → Pendência nos dados de origem, sem efeito nos meses atuais.
