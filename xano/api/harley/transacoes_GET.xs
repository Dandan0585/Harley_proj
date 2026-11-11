query transacoes verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query transacoes {
      return = {type: "list"}
    } as $transacoes1
  }

  response = $transacoes1
  guid = "smXcJbmjfIQO78RFV5-BhBvT3Cs"
}