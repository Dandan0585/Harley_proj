// Update funcionarios record
query "funcionarios/{funcionarios_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int funcionarios_id? filters=min:1
    dblink {
      table = "funcionarios"
    }
  }

  stack {
    db.edit funcionarios {
      field_name = "id"
      field_value = $input.funcionarios_id
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
  guid = "rzITo5QLNxz9AWDX4_5bIn9Sow8"
}