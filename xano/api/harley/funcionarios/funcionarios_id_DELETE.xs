// Delete funcionarios record
query "funcionarios/{funcionarios_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int funcionarios_id? filters=min:1
  }

  stack {
    db.del funcionarios {
      field_name = "id"
      field_value = $input.funcionarios_id
    }
  }

  response = null
  guid = "_a3JLAnpbXW3i6Cn3uKylZaGlXQ"
}