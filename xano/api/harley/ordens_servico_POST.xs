// Add ordens_servico record
query ordens_servico verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "ordens_servico"
    }
  }

  stack {
    db.add ordens_servico {
      enforce_hidden_fields = false
      data = {
        id_moto_cliente: $input.id_moto_cliente
        id_funcionario : $input.id_funcionario
        data_abertura  : $input.data_abertura
        status         : $input.status
      }
    } as $model
  }

  response = $model
  guid = "kXOrEfwXPinaBKxLo65GY_RpMFA"
}