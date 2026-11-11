// Itens das Notas de Entrada de Mercadorias
table itens_compra_estoque {
  auth = false

  schema {
    int id
  
    // Relacionamento com a tabela de Entrada_Mercadoria
    int id_entrada
  
    // Relacionamento com a tabela de Produtos
    int id_produto
  
    int quantidade
    decimal valor_unitario
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  guid = "xC1-dzl-XgnJyKeboyB_lxPCgUQ"
}