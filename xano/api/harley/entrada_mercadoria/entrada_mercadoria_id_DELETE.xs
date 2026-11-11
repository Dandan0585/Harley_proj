// Delete entrada_mercadoria record
query "entrada_mercadoria/{entrada_mercadoria_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int entrada_mercadoria_id? filters=min:1
  }

  stack {
    db.del entrada_mercadoria {
      field_name = "id"
      field_value = $input.entrada_mercadoria_id
    }
  }

  response = null
  guid = "dXME2faU8e6mWA-rsCa__DZ4plY"
}