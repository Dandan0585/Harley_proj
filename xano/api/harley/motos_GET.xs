// Retorna a lista de motos com filtros opcionais.
query motos verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
    // Filtro por ID do cliente
    int cliente_id?
  
    // Filtro por status (ex: "Em estoque", "Vendido")
    text status?
  
    // Filtro por disponibilidade em estoque
    bool em_estoque?
  
    // Filtro por marca
    text marca?
  
    // Filtro por modelo
    text modelo?
  
    // Filtro por ano
    int ano?
  }

  stack {
    // Busca registros na tabela motos aplicando filtros apenas se informados (ignore if empty/null)
    // Suporta filtros por cliente, status, disponibilidade (em_estoque), marca, modelo e ano
    db.query motos {
      where = $db.motos.cliente_id ==? $input.cliente_id && $db.motos.status ==? $input.status && $db.motos.em_estoque ==? $input.em_estoque && $db.motos.marca ==? $input.marca && $db.motos.modelo ==? $input.modelo && $db.motos.ano ==? $input.ano
      return = {type: "list"}
    } as $motos
  }

  response = $motos
  guid = "CTNwq0gHc8QPK5pXuWHuaG8e2TU"
}