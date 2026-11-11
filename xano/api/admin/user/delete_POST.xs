// Deletes a user account. Used by the admin "Usuários do sistema" page.
query "user/delete" verb=POST {
  api_group = "Admin"
  auth = "user"

  input {
    int id?
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok

    precondition ($input.id != $auth.id) {
      error_type = "inputerror"
      error = "Você não pode excluir a própria conta."
    }

    db.del user {
      field_name = "id"
      field_value = $input.id
    }
  }

  response = {message: {"success": "true"}}
  tags = ["harley-store"]
  guid = "hs_admin_user_delete_v1"
}