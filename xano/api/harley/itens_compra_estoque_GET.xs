query itens_compra_estoque verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query itens_compra_estoque {
      return = {type: "list"}
    } as $itens_compra_estoque1
  }

  response = $itens_compra_estoque1
  guid = "UZs8GVhcm9wcu9VnEm_pg5P4iAE"
}