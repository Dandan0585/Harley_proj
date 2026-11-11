query motos_clientes verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query motos_clientes {
      return = {type: "list"}
    } as $motos_clientes1
  }

  response = $motos_clientes1
  guid = "WJq7HxG5dDJnZyk5nZ60kRpcqjs"
}