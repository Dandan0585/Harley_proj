// Add fornecedores record
query fornecedores verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "fornecedores"
    }
  }

  stack {
    db.add fornecedores {
      enforce_hidden_fields = false
      data = {
        nome_fornecedor: $input.nome_fornecedor
        cnpj           : $input.cnpj
        contato        : $input.contato
      }
    } as $model
  }

  response = $model
  guid = "RgBIUlQ6fJiwfueTcFwlubW6qHM"
}