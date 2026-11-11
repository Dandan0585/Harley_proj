// Tabela de Motos dos Clientes
table motos_clientes {
  auth = false

  schema {
    int id
  
    // Relacionamento com a tabela de Clientes
    int id_cliente
  
    text modelo
    text placa filters=trim
    text chassi filters=trim
    text imagem? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "placa"}]}
    {type: "btree|unique", field: [{name: "chassi"}]}
  ]

  guid = "zkiF5wJEqNUGsDsAiRTW9YMnpRA"
}