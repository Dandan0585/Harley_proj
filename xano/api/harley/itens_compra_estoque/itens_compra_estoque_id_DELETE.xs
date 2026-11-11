// Delete itens_compra_estoque record
query "itens_compra_estoque/{itens_compra_estoque_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_compra_estoque_id? filters=min:1
  }

  stack {
    db.del itens_compra_estoque {
      field_name = "id"
      field_value = $input.itens_compra_estoque_id
    }
  }

  response = null
  guid = "VORYm3accH0_1jf8-eLep8QphaE"
}