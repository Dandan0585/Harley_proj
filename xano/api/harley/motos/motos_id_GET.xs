// Retorna os detalhes de uma moto específica através do seu ID.
query "motos/{motos_id}" verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    // ID único da moto para consulta
    int motos_id
  }

  stack {
    // Busca o registro na tabela motos pelo ID fornecido
    db.get motos {
      field_name = "id"
      field_value = $input.motos_id
    } as $moto
  }

  response = $moto
  guid = "L0dARiJc_1q179Xsw37insHEcp4"
}