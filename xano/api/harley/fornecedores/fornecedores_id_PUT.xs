// Update fornecedores record
query "fornecedores/{fornecedores_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int fornecedores_id? filters=min:1
    dblink {
      table = "fornecedores"
    }
  }

  stack {
    db.edit fornecedores {
      field_name = "id"
      field_value = $input.fornecedores_id
      enforce_hidden_fields = false
      data = {
        nome_fornecedor: $input.nome_fornecedor
        cnpj           : $input.cnpj
        contato        : $input.contato
      }
    } as $model
  }

  response = $model
  guid = "tJ6gP88AYzMgIF-OKbpVAteQnQo"
}