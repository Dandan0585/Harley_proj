// Exclui um registro de moto pelo seu ID.
query "motos/{motos_id}" verb=DELETE {
  api_group = "HARLEY"
  auth = "user"

  input {
    // ID da moto a ser excluída do sistema
    int motos_id
  }

  stack {
    // Remove definitivamente o registro da tabela motos
    db.del motos {
      field_name = "id"
      field_value = $input.motos_id
    }
  }

  response = "Registro excluído com sucesso."
  guid = "Bju_Y7sfHGKgXdnSO2NLUVxtabI"
}