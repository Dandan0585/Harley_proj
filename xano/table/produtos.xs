// Tabela de Produtos e Peças
table produtos {
  auth = false

  schema {
    int id
    text nome_produto
    text descricao?
    text categoria
    int estoque_qtd?
    decimal preco_venda
    text imagem? filters=trim
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  guid = "G2b629KCGrzx-9OR6uZkD3o_lP8"
}