// Add itens_compra_estoque record
query itens_compra_estoque verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "itens_compra_estoque"
    }
  }

  stack {
    db.add itens_compra_estoque {
      enforce_hidden_fields = false
      data = {
        id_entrada    : $input.id_entrada
        id_produto    : $input.id_produto
        quantidade    : $input.quantidade
        valor_unitario: $input.valor_unitario
      }
    } as $model
  }

  response = $model
  guid = "oUEDuCJbk9Pek7kD6wMneSsVngc"
}