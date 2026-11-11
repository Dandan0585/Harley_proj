// Tabela de Fornecedores da concessionária
table fornecedores {
  auth = false

  schema {
    int id
    text nome_fornecedor
    text cnpj filters=trim
    text contato?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cnpj"}]}
  ]

  guid = "pG4N0r6OekcVmmKTrHMIk6C3zrg"
}