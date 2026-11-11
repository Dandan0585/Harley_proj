## ADDED Requirements

### Requirement: Cancelamento da cobrança no Asaas
Ao cancelar uma venda com cobrança no Asaas que ainda não foi paga ("Aguardando pagamento" ou "Vencido"), o sistema SHALL cancelar também a cobrança no Asaas e passar o pagamento da venda a "Cobrança cancelada". Se a cobrança não puder ser cancelada no Asaas, a venda MUST ser cancelada mesmo assim, e o funcionário MUST ser avisado para cancelar a cobrança no painel do Asaas. Se a venda já estiver "Pago", o cancelamento MUST seguir normalmente, e o sistema MUST avisar que o estorno deve ser feito no painel do Asaas.

#### Scenario: Cancelar venda com boleto em aberto
- **WHEN** o funcionário cancela uma venda com boleto "Aguardando pagamento"
- **THEN** a venda fica cancelada, o estoque é devolvido, o boleto é cancelado no Asaas e o pagamento fica "Cobrança cancelada"

#### Scenario: Cancelar venda já paga
- **WHEN** o funcionário cancela uma venda "Pago"
- **THEN** a venda fica cancelada, o estoque é devolvido e o sistema avisa que o estorno deve ser feito no painel do Asaas

#### Scenario: Asaas fora do ar no cancelamento
- **WHEN** o funcionário cancela uma venda com cobrança em aberto e o Asaas não responde
- **THEN** a venda fica cancelada, o estoque é devolvido e o sistema avisa para cancelar a cobrança no painel do Asaas
