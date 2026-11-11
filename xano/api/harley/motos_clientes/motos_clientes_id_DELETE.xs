// Delete motos_clientes record
query "motos_clientes/{motos_clientes_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int motos_clientes_id? filters=min:1
  }

  stack {
    db.del motos_clientes {
      field_name = "id"
      field_value = $input.motos_clientes_id
    }
  }

  response = null
  guid = "RZctDyBVBNkeYi8gBkUjgabvKus"
}