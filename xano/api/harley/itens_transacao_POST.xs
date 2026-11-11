// Add itens_transacao record
query itens_transacao verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "itens_transacao"
    }
  }

  stack {
    db.add itens_transacao {
      enforce_hidden_fields = false
      data = {
        created_at    : "now"
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
  guid = "6KfU5l-MoDAhtlRDR3gSv-2jviE"
}