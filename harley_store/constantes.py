"""
Listas fixas usadas pelas telas (opções de seleção).

Os dados ficam no Xano; o esquema real das tabelas está espelhado em
`xano/table/*.xs`. Estas listas são só as opções que o app oferece nos
formulários. Para acrescentar uma opção, basta incluí-la aqui.
"""

# Tipo do funcionário (tabela funcionarios, campo `tipo`).
# A tela de Ordens de serviço só oferece como mecânico quem é MECANICO.
TIPOS_FUNCIONARIO = ["VENDEDOR", "MECANICO", "GERENTE"]

# Tipo da venda (tabela transacoes, campo `tipo_transacao`): a tela de Vendas
# oferece só estes, e o servidor recusa outros (vendas_servico.registrar_venda).
# MOTO = peças e serviços para a moto do cliente; conta no faturamento de
# produtos. A moto da loja é vendida em Produtos > Motos.
# COMPRA e ORDEM_SERVICO existem só em vendas antigas: compra tem a tela
# Compras, e a OS entra no faturamento quando é concluída.
TIPOS_VENDA = ["BALCAO", "PECAS", "MOTO"]

# Situação da ordem de serviço (tabela ordens_servico, campo `status`).
STATUS_OS = ["ABERTA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"]
