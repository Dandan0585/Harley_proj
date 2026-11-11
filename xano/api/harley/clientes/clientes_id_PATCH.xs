// Edit clientes record
query "clientes/{clientes_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    int clientes_id? filters=min:1
    dblink {
      table = "clientes"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch clientes {
      field_name = "id"
      field_value = $input.clientes_id
      data = `$input|pick:($raw_input|keys)`
    } as $model
  }

  response = $model
  guid = "txuGadMkRuJonLwBVoVRAxAu47o"
}