// Administrador define uma nova senha para uma conta (substitui o
// "esqueci minha senha" sem confirmação, que permitia a qualquer pessoa
// trocar a senha de qualquer conta).
query "user/set-password" verb=POST {
  api_group = "Admin"
  auth = "user"

  input {
    int id
    text password filters=trim|min:8
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok
  
    db.edit user {
      field_name = "id"
      field_value = $input.id
      data = {password: $input.password}
    } as $usuario
  }

  response = {id: $usuario.id}
  tags = ["harley-store"]
  guid = "UoHSj7LaOaXFJfQOw4pDMcyzUx8"
}