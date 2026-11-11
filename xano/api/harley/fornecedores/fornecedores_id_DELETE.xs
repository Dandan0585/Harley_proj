// Delete fornecedores record
query "fornecedores/{fornecedores_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int fornecedores_id? filters=min:1
  }

  stack {
    db.del fornecedores {
      field_name = "id"
      field_value = $input.fornecedores_id
    }
  }

  response = null
  guid = "rpP4DKvv8J61q2A61HyV1TdNDpU"
}