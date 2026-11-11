// Generates a one-time reset code for a user, without sending Xano's own
// email — the caller (Harley Store app) sends its own branded email using
// the returned token.
query "reset/request-code" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    email email? filters=trim|lower
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok

    // Generate a one-time magic token (reuses the existing Quick Start function)
    function.run "Quick Start/generate_magic_link" {
      input = {email: $input.email}
    } as $token_and_email
  
    // Check that the token was created
    precondition ($token_and_email != null) {
      error = "Reset code could not be created. Try again."
    }
  }

  response = {
    token: $token_and_email.token
    email: $token_and_email.email
    name : $token_and_email.name
  }

  tags = ["xano:quick-start"]
  guid = "hs_request_code_v1"
}