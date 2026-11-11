## ADDED Requirements

### Requirement: Data de conclusão da OS
Ao mudar a situação de uma OS para CONCLUIDA, o sistema SHALL gravar a data e a hora da conclusão e informar o valor da OS que entrou no faturamento do dia. Se a OS sair da situação CONCLUIDA, a data de conclusão MUST ser apagada. Se o servidor de dados ainda não tiver o campo da data de conclusão, a tela MUST avisar que a OS não entra no faturamento.

#### Scenario: Concluir uma OS
- **WHEN** o funcionário muda a situação de uma OS para CONCLUIDA
- **THEN** aparece "OS nº <número> concluída: R$ <valor> (peças + mão de obra) no faturamento de hoje."

#### Scenario: Reabrir uma OS concluída
- **WHEN** o funcionário muda uma OS de CONCLUIDA para EM_ANDAMENTO
- **THEN** a data de conclusão é apagada e o valor da OS sai do faturamento
