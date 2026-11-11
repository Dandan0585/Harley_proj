// Edit itens_transacao record
query "itens_transacao/{itens_transacao_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_transacao_id? filters=min:1
    dblink {
      table = "itens_transacao"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch itens_transacao {
      field_name = "id"
      field_value = $input.itens_transacao_id
      data = `$input|pick:($raw_input|keys)`
    } as $model
  }

  response = $model
  guid = "FO4RF1zEyYV94kLut6owRkDz0Fs"
}