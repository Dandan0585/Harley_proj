query ordens_servico verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query ordens_servico {
      return = {type: "list"}
    } as $ordens_servico1
  }

  response = $ordens_servico1
  guid = "t8mJw3jdrYs81D8HcjBMtstej6I"
}