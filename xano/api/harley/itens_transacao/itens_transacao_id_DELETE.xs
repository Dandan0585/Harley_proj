// Delete itens_transacao record
query "itens_transacao/{itens_transacao_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_transacao_id? filters=min:1
  }

  stack {
    db.del itens_transacao {
      field_name = "id"
      field_value = $input.itens_transacao_id
    }
  }

  response = null
  guid = "Ur1aaxEy2Ezf5oDtdUSqQAPKFKM"
}