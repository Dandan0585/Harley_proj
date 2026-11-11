// Get transacoes record
query "transacoes/{transacoes_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int transacoes_id? filters=min:1
  }

  stack {
    db.get transacoes {
      field_name = "id"
      field_value = $input.transacoes_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "CK-eTIHmqx6n_hnVNgPWyvu3fmg"
}