// Registra uma movimentação de estoque
query movimentacoes_estoque verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    dblink {
      table = "movimentacoes_estoque"
    }
  }

  stack {
    db.add movimentacoes_estoque {
      data = {
        created_at   : "now"
        produto_id   : $input.produto_id
        quantidade   : $input.quantidade
        saldo_apos   : $input.saldo_apos
        origem       : $input.origem
        referencia_id: $input.referencia_id
        usuario      : $input.usuario
      }
    } as $model
  }

  response = $model
  guid = "LAEWACQBb7Vf-gzFyziaJB0p4_A"
}