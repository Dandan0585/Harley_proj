// Edit ordens_servico record
query "ordens_servico/{ordens_servico_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    int ordens_servico_id? filters=min:1
    dblink {
      table = "ordens_servico"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch ordens_servico {
      field_name = "id"
      field_value = $input.ordens_servico_id
      data = `$input|pick:($raw_input|keys)`
    } as $model
  }

  response = $model
  guid = "OPtJ26XUjo9sqEUEI7ZzKmxSWm4"
}