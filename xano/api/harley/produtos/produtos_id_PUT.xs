// Update produtos record
query "produtos/{produtos_id}" verb=PUT {
  api_group = "HARLEY"
  auth = "user"

  input {
    int produtos_id? filters=min:1
    dblink {
      table = "produtos"
    }
  }

  stack {
    db.edit produtos {
      field_name = "id"
      field_value = $input.produtos_id
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
  guid = "-I-E3WvkRO02aseizY2JNJMKvBI"
}