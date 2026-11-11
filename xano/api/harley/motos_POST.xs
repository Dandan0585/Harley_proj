// Cria um novo registro de moto na tabela 'motos'.
// Este endpoint recebe dados da moto e opcionalmente metadados de imagem.
query motos verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    // ID do cliente vinculado (pode ser null se for estoque da concessionária)
    int? cliente_id?
  
    // Marca da moto (ex: Harley-Davidson)
    text marca
  
    // Modelo da moto (ex: Iron 883)
    text modelo
  
    // Ano de fabricação
    int ano
  
    // Cor da moto (opcional)
    text cor?
  
    // Placa da moto (opcional)
    text placa?
  
    // Chassi da moto (opcional)
    text chassi?
  
    // Quilometragem atual (opcional)
    int quilometragem?
  
    // Status (ex: "Em estoque", "Vendido")
    text status?
  
    // Se está em estoque (true/false)
    bool em_estoque?
  
    // Metadados da imagem enviados pelo endpoint de upload
    json? foto?
  
    // Preço de compra (opcional)
    decimal preco_compra?
  
    // Preço de venda (opcional)
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
    // Adiciona o novo registro na tabela motos com os dados fornecidos
    db.add motos {
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
        created_at   : now
      }
    } as $moto
  }

  response = $moto
  guid = "2ehA1tq9ap981L0Enr_W13885nE"
}