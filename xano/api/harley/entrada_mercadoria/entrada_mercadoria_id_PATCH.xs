// Edit entrada_mercadoria record
query "entrada_mercadoria/{entrada_mercadoria_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    int entrada_mercadoria_id? filters=min:1
    dblink {
      table = "entrada_mercadoria"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch entrada_mercadoria {
      field_name = "id"
      field_value = $input.entrada_mercadoria_id
      data = `$input|pick:($raw_input|keys)`
    } as $model
  }

  response = $model
  guid = "ZzR1dswMK9kBjcTRm2Z2TkCeHK8"
}