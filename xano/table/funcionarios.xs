// Tabela de Funcionários (Vendedores, Mecânicos, Gerentes)
table funcionarios {
  auth = false

  schema {
    int id
    text nome_funcionario
    text cargo
  
    // Tipo pode ser: VENDEDOR, MECANICO, GERENTE
    text tipo
  
    text contato?
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  guid = "HJWm0cncbA52UUslYcCWhxODb4M"
}