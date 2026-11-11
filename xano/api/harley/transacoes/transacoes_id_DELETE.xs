// Delete transacoes record
query "transacoes/{transacoes_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int transacoes_id? filters=min:1
  }

  stack {
    db.del transacoes {
      field_name = "id"
      field_value = $input.transacoes_id
    }
  }

  response = null
  guid = "lgO5z3RgFFtkHDgHMOr-seB18us"
}