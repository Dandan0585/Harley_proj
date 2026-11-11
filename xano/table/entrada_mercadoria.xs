// Registro de Entrada de Mercadorias (Fornecimento)
table entrada_mercadoria {
  auth = false

  schema {
    int id
  
    // Relacionamento com a tabela de Fornecedores
    int id_fornecedor
  
    timestamp data_entrada?=now
    decimal valor_total?
  
    // Descrição dos itens pedidos ao fornecedor (editável na tela Compras)
    text descricao? filters=trim
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  guid = "TROYX6aw69oEPepfYciv6KlYY2g"
}