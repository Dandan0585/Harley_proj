// Simulação da View SQL 'vw_resumo_operacoes'
// Consolida transações e entradas de mercadoria para relatórios
// Retorna um resumo consolidado de transações e entradas de mercadoria
function "relatorio/resumo_operacoes" {
  input {
  }

  stack {
    // 1. Buscar Transações com Joins
    db.query transacoes {
      join = {
        cliente    : {
          table: "clientes"
          type : "left"
          where: $db.transacoes.id_cliente == $db.clientes.id
        }
        funcionario: {
          table: "funcionarios"
          where: $db.transacoes.id_funcionario == $db.funcionarios.id
        }
      }
    
      eval = {
        origem       : $db["TRANSAÇÃO"]
        identificador: $db.transacoes.id
        tipo         : $db.transacoes.tipo_transacao
        cliente      : $db.clientes.nome_cliente
        responsavel  : $db.funcionarios.nome_funcionario
        data         : $db.transacoes.data_transacao
        valor        : $db.transacoes.valor_total
      }
    
      return = {type: "list"}
    } as $lista_transacoes
  
    // 2. Buscar Entradas de Mercadoria com Joins
    db.query entrada_mercadoria {
      join = {
        fornecedor: {
          table: "fornecedores"
          where: $db.entrada_mercadoria.id_fornecedor == $db.fornecedores.id
        }
      }
    
      eval = {
        origem       : $db["ENTRADA DE MERCADORIA"]
        identificador: $db.entrada_mercadoria.id
        tipo         : $db["COMPRA ESTOQUE"]
        cliente      : $db.null
        responsavel  : $db.fornecedores.nome_fornecedor
        data         : $db.entrada_mercadoria.data_entrada
        valor        : $db.entrada_mercadoria.valor_total
      }
    
      return = {type: "list"}
    } as $lista_entradas
  
    // 3. Unificar os resultados (Simulando UNION ALL)
    var $resultado {
      value = $lista_transacoes|merge:$lista_entradas
    }
  }

  response = $resultado
  guid = "m6f9XsnJTXdkMLtnL5dy9U9cunA"
}