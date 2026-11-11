// Query all itens_transacao records
query itens_transacao verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query itens_transacao {
      return = {type: "list"}
    } as $model
  }

  response = $model
  guid = "9eLsMjrATKcEvPFdGU8F01MoYtE"
}