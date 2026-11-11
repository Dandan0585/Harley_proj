// Stores individual items associated with a transaction.
table itens_transacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    // Reference to the transaction this item belongs to.
    int transacao_id? {
      table = "transacoes"
    }
  
    // Reference to the product or item sold.
    int produto_id? {
      table = "produtos"
    }
  
    // Moto da loja vendida neste item (0/vazio = não é moto da loja).
    int moto_id? {
      table = "motos"
    }
  
    // Description of the item.
    text descricao? filters=trim
  
    // Quantity of the item.
    int quantidade?
  
    // Unit price of the item.
    decimal valor_unitario?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "I_un9pAorajQmorqzmwzbtPic0U"
}