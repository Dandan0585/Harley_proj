## Purpose

Mostra, em cada compra, o que foi pedido ao fornecedor, com uma descrição gerada a partir dos itens e que a equipe pode reescrever.

## ADDED Requirements

### Requirement: Descrição gerada ao finalizar a compra
Ao finalizar uma compra, o sistema SHALL gravar uma descrição com a quantidade e o nome de cada item, no formato "2x Pneu Traseiro; 10x Óleo 10W30", com no máximo 500 caracteres.

#### Scenario: Compra com dois itens
- **WHEN** o funcionário finaliza uma compra de 2 pneus traseiros e 10 óleos 10W30
- **THEN** a compra é gravada com a descrição "2x Pneu Traseiro; 10x Óleo 10W30"

### Requirement: Coluna Descrição na lista
A lista de compras SHALL ter a coluna "Descrição", com a descrição gravada. Uma compra sem descrição gravada MUST mostrar a descrição montada pelos itens, e uma compra sem itens mostra "—".

#### Scenario: Compra antiga
- **WHEN** a lista mostra uma compra registrada antes da descrição existir
- **THEN** a coluna mostra a quantidade e o nome dos itens dessa compra

### Requirement: Edição da descrição
A equipe SHALL poder reescrever a descrição pelo lápis ao lado dela, com no máximo 500 caracteres. Salvar a descrição vazia MUST fazer a coluna voltar a mostrar a descrição montada pelos itens. Se o servidor de dados ainda não tiver o campo da descrição, a tela MUST avisar que é preciso atualizar o servidor de dados.

#### Scenario: Reescrever a descrição
- **WHEN** o funcionário abre o lápis, escreve "Pedido de reposição para a revisão de outubro" e salva
- **THEN** a lista passa a mostrar esse texto e aparece a confirmação de que a descrição foi atualizada

#### Scenario: Compra excluída por outra pessoa
- **WHEN** o funcionário salva a descrição de uma compra que outra pessoa acabou de excluir
- **THEN** aparece a mensagem de que a compra não existe mais
