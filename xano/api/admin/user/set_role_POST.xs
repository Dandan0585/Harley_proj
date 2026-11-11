// Administrador muda o perfil de uma conta ("admin" ou "member").
query "user/set-role" verb=POST {
  api_group = "Admin"
  auth = "user"

  input {
    int id
    text role filters=trim|lower
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok
  
    precondition ($input.role == "admin" || $input.role == "member") {
      error_type = "inputerror"
      error = "Perfil inválido."
    }
  
    precondition ($input.id != $auth.id) {
      error_type = "inputerror"
      error = "Você não pode alterar o próprio perfil."
    }
  
    db.edit user {
      field_name = "id"
      field_value = $input.id
      data = {role: $input.role}
    } as $usuario
  }

  response = {id: $usuario.id, role: $usuario.role}
  tags = ["harley-store"]
  guid = "jlkC4hIAMxQzouzVZ05fC9fhwSc"
}