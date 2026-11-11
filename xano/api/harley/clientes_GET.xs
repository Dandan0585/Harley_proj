query clientes verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query clientes {
      return = {type: "list"}
    } as $clientes1
  }

  response = $clientes1
  guid = "VOtnM_t6-lOTRj4zmcwmPKjOmlA"
}