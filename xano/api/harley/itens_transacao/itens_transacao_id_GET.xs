// Get itens_transacao record
query "itens_transacao/{itens_transacao_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_transacao_id? filters=min:1
  }

  stack {
    db.get itens_transacao {
      field_name = "id"
      field_value = $input.itens_transacao_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "yEnvVH-yND4YpIbWiVKebh_-mzU"
}