// Tabela de Clientes da concessionária
table clientes {
  auth = false

  schema {
    int id
    text nome_cliente
    text cpf_cnpj filters=trim
    text telefone?
    text email?
    text endereco?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cpf_cnpj"}]}
  ]

  guid = "YyjjQVmdgREHIFwb0Tzdz6Nhess"
}