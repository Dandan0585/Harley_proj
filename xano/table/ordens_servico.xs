// Registro de Ordens de Serviço (Oficina)
table ordens_servico {
  auth = false

  schema {
    int id
  
    // Relacionamento com Moto do Cliente
    int id_moto_cliente
  
    // Mecânico Responsável
    int id_funcionario
  
    timestamp data_abertura?=now
  
    // Status: ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA
    text status?=ABERTA

    // Quando a OS foi marcada como CONCLUIDA (entra no faturamento desse dia)
    timestamp data_conclusao?
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  guid = "RSYBlXIs7fG2az0lpnw1Q09idmI"
}