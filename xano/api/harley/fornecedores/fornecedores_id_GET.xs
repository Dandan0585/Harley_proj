// Get fornecedores record
query "fornecedores/{fornecedores_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int fornecedores_id? filters=min:1
  }

  stack {
    db.get fornecedores {
      field_name = "id"
      field_value = $input.fornecedores_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "PzV56KoaIgdLVaU0N7612zJ3So8"
}