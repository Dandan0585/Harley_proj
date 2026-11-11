// Tabela de motos para controle de estoque e vendas da concessionária.
table motos {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp updated_at?
  
    // Referência ao cliente (se a moto pertencer a um)
    int cliente_id? {
      table = "clientes"
    }
  
    text marca filters=trim
    text modelo filters=trim
    int ano
    text cor?
    text placa?
    text chassi?
    int quilometragem?
    text status?="Em estoque"
    bool em_estoque?=true
    image? foto?
    decimal preco_compra?
    decimal preco_venda?
    timestamp data_entrada?
    timestamp data_saida?
    text observacoes?
  
    // RENAVAM (11 dígitos), quando a moto é emplacada
    text renavam? filters=trim
  
    // Cilindrada em cm³ (ex.: 1868)
    int cilindrada?
  
    // Onde a moto está: showroom, oficina, pátio, outra loja...
    text localizacao? filters=trim
  
    // Fotos adicionais: lista de objetos de imagem (a principal é `foto`)
    json fotos?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "cliente_id"}]}
  ]

  guid = "4FltZcmQsW8uoxrdn0ofichqu7E"
}