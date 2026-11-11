// Query all funcionarios records
query funcionarios verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query funcionarios {
      return = {type: "list"}
    } as $model
  }

  response = $model
  guid = "tyozI91eWzhBaGF1RyU6Co5knPw"
}