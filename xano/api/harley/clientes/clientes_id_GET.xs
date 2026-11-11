// Get clientes record
query "clientes/{clientes_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int clientes_id? filters=min:1
  }

  stack {
    db.get clientes {
      field_name = "id"
      field_value = $input.clientes_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "4__2DFx4U_YtOxsE4DJl0upevrg"
}