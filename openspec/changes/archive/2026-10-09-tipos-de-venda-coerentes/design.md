## Context

A lista de tipos da venda é `TIPOS_TRANSACAO` em `harley_store/constantes.py`, usada só pela tela de Vendas (`pages/vendas.py` e `state/vendas_state.py`). O tipo escolhido chega a `vendas_servico.registrar_venda` sem nenhuma conferência: como o Reflex gera o setter `set_tipo_transacao`, qualquer texto enviado pelo websocket seria gravado. O Painel já trata os tipos (ver `dashboard_state.py`): `COMPRA` e `ORDEM_SERVICO` ficam fora do faturamento, e os itens de qualquer venda contam como produtos.

As correções de dados mexem no Xano compartilhado entre desenvolvimento e produção (ver proposal.md, What Changes).

## Goals / Non-Goals

**Goals:**
- Uma só lista de tipos válidos, usada pela tela e pela regra do servidor.
- Correções de dados repetíveis, com prévia e confirmação, sem gravar em dobro se rodarem de novo.

**Non-Goals:**
- Mudar o esquema do Xano ou a regra de faturamento do Painel.
- Converter as vendas antigas dos tipos que saem da tela.

## Decisions

### D1. `TIPOS_VENDA` substitui `TIPOS_TRANSACAO` em `constantes.py`
A lista passa a ser `["BALCAO", "PECAS", "MOTO"]`, com um comentário explicando que `COMPRA` e `ORDEM_SERVICO` existem só em vendas antigas. **Alternativa:** manter `TIPOS_TRANSACAO` completa e filtrar na tela. Foi descartada porque deixaria duas fontes para a mesma regra, e a lista completa não tem mais outro uso.

### D2. A recusa fica em `vendas_servico.registrar_venda`, antes de mexer no estoque
Tipo fora de `TIPOS_VENDA` levanta `FalhaVenda("Tipo de venda inválido: ...")` antes da baixa de estoque. Assim a regra vale para a tela e para qualquer pedido direto pelo websocket, e fica testável sem o Xano. **Alternativa:** validar só no state. Foi descartada porque a interface não é mecanismo de segurança (AGENTS.md).

### D3. Correções de dados por um script versionado com prévia e confirmação
`scripts/corrigir_dados_tipos_de_venda.py` segue o padrão de `scripts/cadastrar_motos_catalogo.py`: mostra o que vai fazer e só grava após "s". Cada correção confere o estado antes de agir, então rodar de novo não repete nada:
- **Venda nº 8:** usa `vendas_servico.cancelar_venda`, a mesma regra da tela. Venda já cancelada é pulada. Como ela não tem itens, não há devolução de estoque.
- **Moto da Helena:** criada com `xano.criar("motos", ...)` e o registro completo, no mesmo formato de `MotosLojaState.salvar`. É pulada se já existir moto da loja com a placa HIJ8K90 ou o mesmo chassi.
- **Moto nº 15:** lida com `xano.buscar` e regravada com o registro completo, porque o PATCH do Xano substitui o registro inteiro. Só muda `preco_compra`, e só se ainda estiver em R$ 119,95.

**Alternativa:** corrigir pelas telas do app. Foi descartada porque o cadastro pela tela não deixa registro de por que e quando a correção foi feita, e o script fica no histórico do Git.

### D4. Campos sem informação ficam vazios
Ano, cor e quilometragem da moto da Helena são gravados vazios (ano 0, como a tela grava quando o campo fica em branco). A origem da moto fica nas observações. Ela fica `em_estoque` verdadeiro, pois "Em preparação" não tira a moto do estoque.

## Risks / Trade-offs

- [O Xano recusa ano 0 no campo obrigatório `ano`] → o script mostra o erro e para, sem gravar as outras correções da moto; o grupo decide o valor antes de rodar de novo.
- [A mesma moto passa a existir como moto da cliente e como moto da loja] → é proposital (decisão do grupo): a OS nº 8 continua apontando para a moto da cliente; a ligação entre as duas tabelas é o problema B do Explore, fora do escopo.
- [O chassi da moto da Helena é fictício, vindo dos dados de exemplo] → é mantido para não perder a correspondência com o cadastro da cliente; pode ser corrigido pela tela quando o chassi real for conhecido.
- [Correção no Xano compartilhado afeta a produção] → a produção está pausada (modo demonstração); o script mostra a prévia antes de gravar.

## Migration Plan

1. Publicar o código (tipos e recusa no servidor) e rodar os testes.
2. Rodar o script, conferir a prévia e confirmar.
3. Conferir no app: venda nº 8 Cancelada com o motivo; Low Rider S da Helena em Produtos > Motos; moto nº 15 com R$ 119.950,00; Estoque de Motos do Painel atualizado.

**Para desfazer:** reverter o commit do código. Os dados se desfazem pelas telas (excluir a moto criada e voltar o preço da nº 15). A venda cancelada não volta a ficar ativa, por regra do sistema.
