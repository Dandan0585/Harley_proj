// Update itens_ordem_servico record
query "itens_ordem_servico/{itens_ordem_servico_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_ordem_servico_id? filters=min:1
    dblink {
      table = "itens_ordem_servico"
    }
  }

  stack {
    db.edit itens_ordem_servico {
      field_name = "id"
      field_value = $input.itens_ordem_servico_id
      enforce_hidden_fields = false
      data = {
        id_os           : $input.id_os
        id_produto      : $input.id_produto
        quantidade      : $input.quantidade
        valor_total_item: $input.valor_total_item
      }
    } as $model
  }

  response = $model
  guid = "TFhCU2WCfbN0_cmVlx_0CSDrZRU"
}