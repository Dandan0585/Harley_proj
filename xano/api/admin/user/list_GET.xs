// Lists all user accounts (id, name, email, created_at) for the admin
// "Usuários do sistema" page. Excludes password and password_reset on purpose.
query "user/list" verb=GET {
  api_group = "Admin"
  auth = "user"

  input {
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok

    db.query user {
      return = {type: "list"}
      output = ["id", "created_at", "name", "email", "role"]
    } as $usuarios
  }

  response = $usuarios
  tags = ["harley-store"]
  guid = "hs_admin_user_list_v1"
}