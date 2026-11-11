// Delete clientes record
query "clientes/{clientes_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int clientes_id? filters=min:1
  }

  stack {
    db.del clientes {
      field_name = "id"
      field_value = $input.clientes_id
    }
  }

  response = null
  guid = "5McA4nV-bm_fmop5auzm3qcJQS4"
}