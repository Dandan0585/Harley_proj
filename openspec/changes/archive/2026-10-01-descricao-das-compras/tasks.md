## 1. Banco de dados (Xano)

- [x] 1.1 Acrescentar `descricao` em `entrada_mercadoria` e nos endpoints POST e PUT, e aplicar com `scripts/aplicar_xano.ps1`; feito em 01/10/2026 (commit `cb9b8ff`), aplicado em 05/10/2026 e verificado no Xano (o campo existe e é devolvido nas compras)

## 2. Tela

- [x] 2.1 Gravar a descrição montada pelos itens ao finalizar a compra; verificado no uso real: as compras nº 15 e 16, de 05/10/2026, têm as descrições "10x Pneu Traseiro 110/90-17" e "1x Jogo de Velas de Ignição"
- [x] 2.2 Mostrar a coluna "Descrição", com a descrição montada pelos itens para as compras antigas; verificado no código de `compras_state.py` e `pages/compras.py` e pelo teste `test_descricao_dos_itens`
- [x] 2.3 Editar a descrição pelo lápis, com o aviso quando o Xano não tem o campo; verificado no código (`salvar_descricao`)
- [x] 2.4 Compilar o app; verificado em 07/10/2026 (`reflex compile` sem erros)
