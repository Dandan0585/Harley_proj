// Get itens_ordem_servico record
query "itens_ordem_servico/{itens_ordem_servico_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_ordem_servico_id? filters=min:1
  }

  stack {
    db.get itens_ordem_servico {
      field_name = "id"
      field_value = $input.itens_ordem_servico_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "y6O0txGf2CWbck6PtQAnfiy6fEI"
}