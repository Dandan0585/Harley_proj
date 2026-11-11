query itens_ordem_servico verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query itens_ordem_servico {
      return = {type: "list"}
    } as $itens_ordem_servico1
  }

  response = $itens_ordem_servico1
  guid = "9Z3r9mDL1wOe0reAwVwEMuoeDww"
}