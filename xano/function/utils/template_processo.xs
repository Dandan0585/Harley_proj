// Função Modelo: Use este padrão para novas lógicas de negócio
// Descrição: Breve explicação do que a função faz
// Retorne sempre um objeto estruturado ou o resultado principal
// Modelo para criação de novas funções com validação e processamento
function "utils/template_processo" {
  input {
    // Defina os inputs com tipos e filtros
    // ID de referência para o processo
    int id_exemplo
  
    // Valor opcional para cálculo
    decimal valor_ajuste?
  }

  stack {
    // 1. Validação (Precondition)
    // Sempre verifique se os dados necessários existem ou são válidos
    db.get produtos {
      field_name = "id"
      field_value = $input.id_exemplo
    } as $registro
  
    precondition ($registro != null) {
      error_type = "notfound"
      error = "O registro de exemplo não foi encontrado."
    }
  
    // 2. Lógica de Negócio
    // Realize cálculos ou transformações de dados
    var $resultado_calculo {
      value = $registro.preco_venda + $input.valor_ajuste
    }
  
    // 3. Persistência (Opcional)
    // Se a função precisar alterar o banco, use db.edit ou db.add
    // db.edit "produtos" { ... }
  
    // 4. Log ou Debug
    // Útil para rastrear o que aconteceu durante o desenvolvimento
    debug.log {
      value = "Processamento concluído para ID: " ~ ($input.id_exemplo|to_text)
    }
  }

  response = {
    sucesso    : true
    dados      : $registro
    valor_final: $resultado_calculo
  }

  guid = "lpd6CEK6vP6YdTIMRu5xL-foVgQ"
}