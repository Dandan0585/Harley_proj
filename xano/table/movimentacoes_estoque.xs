// Histórico de movimentações de estoque, gravado pelo app a cada entrada ou
// saída (venda, cancelamento, peça em OS, compra, ajuste manual...).
table movimentacoes_estoque {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int produto_id? {
      table = "produtos"
    }
  
    // Variação: negativa = saída, positiva = entrada
    int quantidade
  
    // Saldo do produto logo depois da movimentação
    int saldo_apos?
  
    // VENDA, CANCELAMENTO_VENDA, OS, EXCLUSAO_OS, COMPRA, EXCLUSAO_COMPRA, AJUSTE, CADASTRO
    text origem filters=trim
  
    // Id do documento de origem (venda, OS, compra)
    int referencia_id?
  
    // Quem fez (nome do usuário logado)
    text usuario? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "produto_id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "Y3jlkkAZ4srWBjgDwsEHfugx0WY"
}