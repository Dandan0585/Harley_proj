query entrada_mercadoria verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query entrada_mercadoria {
      return = {type: "list"}
    } as $entrada_mercadoria1
  }

  response = $entrada_mercadoria1
  guid = "X7yfgQJXJPVu7JgiDs5eY7k_8uE"
}