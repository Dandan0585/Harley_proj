// Delete produtos record
query "produtos/{produtos_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    int produtos_id? filters=min:1
  }

  stack {
    db.del produtos {
      field_name = "id"
      field_value = $input.produtos_id
    }
  }

  response = null
  guid = "79wWxaXQaZfp5mgYy8atCNdtNxo"
}