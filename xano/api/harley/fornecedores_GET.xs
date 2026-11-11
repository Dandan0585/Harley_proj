query fornecedores verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query fornecedores {
      return = {type: "list"}
    } as $fornecedores1
  }

  response = $fornecedores1
  guid = "7ZhqainQN2j_6NctNTtrAUc2LSI"
}