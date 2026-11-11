// Get itens_compra_estoque record
query "itens_compra_estoque/{itens_compra_estoque_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_compra_estoque_id? filters=min:1
  }

  stack {
    db.get itens_compra_estoque {
      field_name = "id"
      field_value = $input.itens_compra_estoque_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "651ZPoYc-X03Dsjfrdw3L1vKKVQ"
}