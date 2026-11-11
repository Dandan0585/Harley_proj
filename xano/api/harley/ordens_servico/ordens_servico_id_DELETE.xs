// Delete ordens_servico record
query "ordens_servico/{ordens_servico_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int ordens_servico_id? filters=min:1
  }

  stack {
    db.del ordens_servico {
      field_name = "id"
      field_value = $input.ordens_servico_id
    }
  }

  response = null
  guid = "FE5dXuDmt2wDaL_Va3W6TTFyQ20"
}