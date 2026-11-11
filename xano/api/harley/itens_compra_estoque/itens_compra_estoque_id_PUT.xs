// Update itens_compra_estoque record
query "itens_compra_estoque/{itens_compra_estoque_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_compra_estoque_id? filters=min:1
    dblink {
      table = "itens_compra_estoque"
    }
  }

  stack {
    db.edit itens_compra_estoque {
      field_name = "id"
      field_value = $input.itens_compra_estoque_id
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
  guid = "FpljvsaccJC90d6IPXVufuknlzE"
}