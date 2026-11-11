// Add produtos record
query produtos verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "produtos"
    }
  }

  stack {
    db.add produtos {
      enforce_hidden_fields = false
      data = {
        nome_produto: $input.nome_produto
        descricao   : $input.descricao
        categoria   : $input.categoria
        estoque_qtd : $input.estoque_qtd
        preco_venda : $input.preco_venda
      }
    } as $model
  }

  response = $model
  guid = "hIKF5eJ0t7uz449YQProXKoWrU8"
}