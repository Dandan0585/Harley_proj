// Edit itens_ordem_servico record
query "itens_ordem_servico/{itens_ordem_servico_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_ordem_servico_id? filters=min:1
    dblink {
      table = "itens_ordem_servico"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch itens_ordem_servico {
      field_name = "id"
      field_value = $input.itens_ordem_servico_id
      data = `$input|pick:($raw_input|keys)`
    } as $model
  }

  response = $model
  guid = "HFluPYR2iQIIn-mMLslvSOC4PYs"
}