// Retorna o resumo consolidado de transações e entradas (View SQL)
query resumo verb=GET {
  api_group = "Relatorios"
  auth = "user"

  input {
  }

  stack {
    function.run "relatorio/resumo_operacoes" as $relatorio
  }

  response = {
    status          : "success"
    integration_test: "VSCode + Xano + Python: OK!"
    data            : $relatorio
  }

  guid = "u72OmoBPf2PxfNTKNPyo7c2lxH0"
}