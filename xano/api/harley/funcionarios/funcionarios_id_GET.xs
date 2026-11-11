// Get funcionarios record
query "funcionarios/{funcionarios_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int funcionarios_id? filters=min:1
  }

  stack {
    db.get funcionarios {
      field_name = "id"
      field_value = $input.funcionarios_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "4meStHpo-mMRWp4STsXbLf1uskA"
}