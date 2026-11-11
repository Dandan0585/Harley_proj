// Update itens_transacao record
query "itens_transacao/{itens_transacao_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int itens_transacao_id? filters=min:1
    dblink {
      table = "itens_transacao"
    }
  }

  stack {
    db.edit itens_transacao {
      field_name = "id"
      field_value = $input.itens_transacao_id
      enforce_hidden_fields = false
      data = {
        transacao_id  : $input.transacao_id
        produto_id    : $input.produto_id
        moto_id       : $input.moto_id
        descricao     : $input.descricao
        quantidade    : $input.quantidade
        valor_unitario: $input.valor_unitario
      }
    } as $model
  }

  response = $model
  guid = "7kcqVJzzxApFNaBEcPHDGutB3hM"
}