// Add entrada_mercadoria record
query entrada_mercadoria verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "entrada_mercadoria"
    }
  }

  stack {
    db.add entrada_mercadoria {
      enforce_hidden_fields = false
      data = {
        id_fornecedor: $input.id_fornecedor
        data_entrada : $input.data_entrada
        valor_total  : $input.valor_total
        descricao    : $input.descricao
      }
    } as $model
  }

  response = $model
  guid = "bpkPJAQM4DhPubJvbCwwNRgri2Q"
}