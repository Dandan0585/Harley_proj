// Updates a user's email address. Used by the admin "Usuários do sistema" page.
query "user/update-email" verb=POST {
  api_group = "Admin"
  auth = "user"

  input {
    int id?
    email email? filters=trim|lower
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok

    db.edit user {
      field_name = "id"
      field_value = $input.id
      data = {email: $input.email}
    } as $usuario
  }

  response = {
    id        : $usuario.id
    created_at: $usuario.created_at
    name      : $usuario.name
    email     : $usuario.email
    role      : $usuario.role
  }

  tags = ["harley-store"]
  guid = "hs_admin_user_update_email_v1"
}