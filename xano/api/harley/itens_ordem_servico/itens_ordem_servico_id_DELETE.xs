// Delete itens_ordem_servico record
query "itens_ordem_servico/{itens_ordem_servico_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_ordem_servico_id? filters=min:1
  }

  stack {
    db.del itens_ordem_servico {
      field_name = "id"
      field_value = $input.itens_ordem_servico_id
    }
  }

  response = null
  guid = "Dmlf6DhZdKxQm4abQySmdTpDyV0"
}