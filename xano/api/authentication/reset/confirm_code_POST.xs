// Verifies a one-time reset code (created by reset/request-code) and sets
// the new password in a single step. Does not issue an authToken — this is
// not a login, just a password change.
query "reset/confirm-code" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    email email? filters=trim|lower
    text code? filters=trim
    text password? filters=trim|min:8
    text confirm_password? filters=trim
  }

  stack {
    // Só administradores (perfil "admin" na tabela user)
    function.run "Quick Start/enforce_role" {
      input = {user_id: $auth.id, required_role: "admin"}
    } as $perfil_ok

    // Check that the password inputs are matching
    precondition ($input.password == $input.confirm_password) {
      error = "Passwords do not match!"
    }
  
    // Get the user record via email
    db.get user {
      field_name = "email"
      field_value = $input.email
      output = [
        "id"
        "email"
        "name"
        "password_reset.token"
        "password_reset.expiration"
        "password_reset.used"
      ]
    } as $user
  
    // Check to make sure a user with that email exists
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Invalid or expired code."
    }
  
    // Validate the code matches the hashed reset token
    security.check_password {
      text_password = $input.code
      hash_password = $user.password_reset.token
    } as $code_result
  
    // Verify the code check passed
    precondition ($code_result) {
      error_type = "accessdenied"
      error = "Invalid or expired code."
    }
  
    // Check that the reset code has not expired
    precondition ($user.password_reset.expiration > now) {
      error_type = "accessdenied"
      error = "Invalid or expired code."
    }
  
    // Check that the reset code has not already been used
    precondition ($user.password_reset.used == false) {
      error_type = "accessdenied"
      error = "Invalid or expired code."
    }
  
    // Update the password and mark the reset code as used
    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {
        password      : $input.password
        password_reset: {
        token     : $user.password_reset.token
        expiration: $user.password_reset.expiration
        used      : true
      }
      }
    } as $updated_user
  
    // Create an event log for password reset
    function.run "Quick Start/log_event" {
      input = {
        user_id : $user.id
        action  : "reset_password"
        metadata: $updated_user
      }
    } as $event_log
  }

  response = {
    message: {"success": "true", "message": "Password updated"}
  }

  tags = ["xano:quick-start"]
  guid = "hs_confirm_code_v1"
}