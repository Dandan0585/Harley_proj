// Atualiza parcialmente um registro de moto.
query "motos/{motos_id}" verb=PATCH {
  api_group = "HARLEY"
  auth = "user"

  input {
    // ID da moto a ser atualizada
    int motos_id
  
    // ID do cliente vinculado (opcional)
    int? cliente_id?
  
    // Marca da moto
    text marca?
  
    // Modelo da moto
    text modelo?
  
    // Ano de fabricação
    int ano?
  
    // Cor da moto
    text cor?
  
    // Placa da moto
    text placa?
  
    // Chassi da moto
    text chassi?
  
    // Quilometragem atual
    int quilometragem?
  
    // Status (ex: "Em estoque")
    text status?
  
    // Se está em estoque
    bool em_estoque?
  
    // Metadados da imagem (enviados como JSON)
    json? foto?
  
    // Preço de compra
    decimal preco_compra?
  
    // Preço de venda
    decimal preco_venda?
  
    // Data de entrada no estoque
    timestamp data_entrada?
  
    // Data de saída (opcional)
    timestamp? data_saida?
  
    // Observações adicionais
    text observacoes?
  
    text renavam?
    int? cilindrada?
    text localizacao?
    json? fotos?
  }

  stack {
    // Atualiza os campos fornecidos no registro identificado pelo ID
    db.patch motos {
      field_name = "id"
      field_value = $input.motos_id
      data = {
        cliente_id   : $input.cliente_id
        marca        : $input.marca
        modelo       : $input.modelo
        ano          : $input.ano
        cor          : $input.cor
        placa        : $input.placa
        chassi       : $input.chassi
        quilometragem: $input.quilometragem
        status       : $input.status
        em_estoque   : $input.em_estoque
        foto         : $input.foto
        preco_compra : $input.preco_compra
        preco_venda  : $input.preco_venda
        data_entrada : $input.data_entrada
        data_saida   : $input.data_saida
        observacoes  : $input.observacoes
        renavam      : $input.renavam
        cilindrada   : $input.cilindrada
        localizacao  : $input.localizacao
        fotos        : $input.fotos
        updated_at   : now
      }
    } as $moto
  }

  response = $moto
  guid = "EI5XsE61tmHHKFKC4C6UQaivL4c"
}