// Add clientes record
query clientes verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "clientes"
    }
  }

  stack {
    db.add clientes {
      enforce_hidden_fields = false
      data = {
        nome_cliente: $input.nome_cliente
        cpf_cnpj    : $input.cpf_cnpj
        telefone    : $input.telefone
        email       : $input.email
        endereco    : $input.endereco
      }
    } as $model
  }

  response = $model
  guid = "555hR3_UmysBAQM1d0fNxPeWuxo"
}