// Get ordens_servico record
query "ordens_servico/{ordens_servico_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int ordens_servico_id? filters=min:1
  }

  stack {
    db.get ordens_servico {
      field_name = "id"
      field_value = $input.ordens_servico_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "W-qIcOsAvoVa0Z2e000oSeZ_i-8"
}