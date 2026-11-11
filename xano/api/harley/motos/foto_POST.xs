// Gera metadados de imagem a partir de um arquivo enviado.
query "motos/foto" verb=POST {
  api_group = "HARLEY"
  auth = "user"

  input {
    // Arquivo de imagem a ser processado
    file? arquivo
  }

  stack {
    // Cria os metadados da imagem no armazenamento do Xano com acesso público
    storage.create_image {
      value = $input.arquivo
      access = "public"
      filename = $input.arquivo.name
    } as $foto
  
    // Constrói a URL pública baseada no ambiente
    var $base_url {
      value = ($env.$api_baseurl|split:"/api")|first
    }
  
    var $foto_url {
      value = $base_url ~ $foto.path
    }
  }

  response = $foto|set:"url":$foto_url
  guid = "5PLHUor-jAMe5QUazqfIRH6Z414"
}