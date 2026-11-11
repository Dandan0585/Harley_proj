## 1. Documento

- [x] 1.1 Criar a página `/imprimir/[doc_tipo]/[doc_id]`, protegida por login, com a folha A4 genérica; feito em 23/09/2026 (commit `5b1f108`) e verificado em 07/10/2026 no código (`exigir_login` no `on_load` da rota)
- [x] 1.2 Montar os quatro tipos (venda, OS, compra e moto, com recibo ou ficha conforme a situação); verificado no código de `impressao_state.py` e na impressão de vendas ativa, cancelada e antiga feita na change `vendas-com-itens-e-cancelamento` (tarefa 5.2)
- [x] 1.3 Mostrar mensagem para tipo inválido, número inválido ou registro inexistente; verificado no código ("Documento inválido." e "... não encontrada.")

## 2. Botões

- [x] 2.1 Criar o botão de impressão que abre em nova aba e colocá-lo em Vendas, Ordens de serviço, Compras e nos cartões de motos ("Recibo" ou "Ficha"); verificado em 07/10/2026 (botão presente nas quatro telas)
- [x] 2.2 Compilar o app; verificado em 07/10/2026 (`reflex compile` sem erros)
