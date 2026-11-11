// Add funcionarios record
query funcionarios verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "funcionarios"
    }
  }

  stack {
    db.add funcionarios {
      enforce_hidden_fields = false
      data = {
        nome_funcionario: $input.nome_funcionario
        cargo           : $input.cargo
        tipo            : $input.tipo
        contato         : $input.contato
      }
    } as $model
  }

  response = $model
  guid = "FAEWRdlC1uoYSaC7045RCdfPj1Q"
}