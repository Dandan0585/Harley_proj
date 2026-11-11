query produtos verb=GET {
  api_group = "HARLEY"
  auth = "user"

  input {
  }

  stack {
    db.query produtos {
      return = {type: "list"}
    } as $produtos1
  }

  response = $produtos1
  guid = "VOwpLVMPSp1dagCluoKg4AG1Fw4"
}