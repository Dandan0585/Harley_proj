# Importar o banco Harley Store para o workspace "HARLEY" no Xano

Estes 10 arquivos CSV são a tradução exata do `SCRIPT_HARLEY_ATUALIZADO.sql`
(o mesmo banco usado para construir a primeira versão do app Reflex; o esquema
atual das tabelas está espelhado em `xano/table/`),
prontos para importar direto na tela **Database** do seu workspace novo
(`x8ki-letl-twmt.n7.xano.io/workspace/168750-0`).

O plano Free do Xano não libera a Metadata API, então a criação não pode ser
feita por mim via API — mas o import manual abaixo leva poucos minutos.

## Ordem de importação (respeite esta ordem — tabelas "pai" antes das "filhas")

1. `01_fornecedores.csv`
2. `02_produtos.csv`
3. `03_funcionarios.csv`
4. `04_clientes.csv`
5. `05_motos_clientes.csv` (referencia clientes)
6. `06_entrada_mercadoria.csv` (referencia fornecedores)
7. `07_itens_compra_estoque.csv` (referencia entrada_mercadoria e produtos)
8. `08_transacoes.csv` (referencia funcionarios, clientes, motos_clientes)
9. `09_ordens_servico.csv` (referencia motos_clientes e funcionarios)
10. `10_itens_ordem_servico.csv` (referencia ordens_servico e produtos)

Essa ordem garante que os números em colunas como `id_cliente`, `id_produto`
etc. batam certinho com o `id` gerado automaticamente pelo Xano em cada
tabela pai (o Xano numera a partir de 1, na ordem de inserção — igual ao
`IDENTITY(1,1)` do SQL Server original).

## Passo a passo para cada arquivo

1. No menu lateral, clique em **Database**.
2. Clique em **Add Table** → **Import from File** (ou o ícone de importar).
3. Selecione o CSV correspondente.
4. Dê o nome da tabela sem o número/prefixo, exatamente como no SQL original:
   `fornecedores`, `produtos`, `funcionarios`, `clientes`, `motos_clientes`,
   `entrada_mercadoria`, `itens_compra_estoque`, `transacoes`,
   `ordens_servico`, `itens_ordem_servico`.
5. O Xano detecta os tipos automaticamente (texto, número, decimal). Confira:
   - `estoque_qtd`, `quantidade` → **int**
   - `preco_venda`, `valor_total`, `valor_unitario`, `valor_total_item` → **decimal**
   - `data_entrada`, `data_transacao`, `data_abertura` → **timestamp**
6. Clique em **Import/Confirm**.

## Depois de importar as 10 tabelas: transformar as colunas de ID em relacionamentos

Por padrão, colunas como `id_cliente` entram como número simples. Para virar
relacionamento de verdade (Table Reference) no Xano:

1. Abra a tabela (ex.: `motos_clientes`), clique no campo `id_cliente`.
2. Mude o tipo para **Table Reference**, aponte para a tabela `clientes`.
3. Repita para cada FK, seguindo o mapa abaixo:

| Tabela                | Campo FK          | Aponta para        |
|-----------------------|-------------------|---------------------|
| motos_clientes        | id_cliente        | clientes            |
| entrada_mercadoria    | id_fornecedor     | fornecedores        |
| itens_compra_estoque  | id_entrada        | entrada_mercadoria  |
| itens_compra_estoque  | id_produto        | produtos            |
| transacoes            | id_funcionario    | funcionarios        |
| transacoes            | id_cliente        | clientes            |
| transacoes            | id_moto_cliente   | motos_clientes      |
| ordens_servico        | id_moto_cliente   | motos_clientes      |
| ordens_servico        | id_funcionario    | funcionarios        |
| itens_ordem_servico   | id_os             | ordens_servico      |
| itens_ordem_servico   | id_produto        | produtos            |

## Campos com regra de negócio (eram CHECK CONSTRAINT no SQL Server)

O Xano não tem "CHECK constraint" nativo, mas dá para simular com validação
no campo ou em pré-processamento das APIs:

- `produtos.estoque_qtd >= 0`
- `produtos.preco_venda >= 0`
- `funcionarios.tipo` só pode ser `VENDEDOR`, `MECANICO` ou `GERENTE`
- `transacoes.tipo_transacao` só pode ser `MOTO`, `PECAS`, `BALCAO`, `COMPRA` ou `ORDEM_SERVICO`
- `ordens_servico.status` só pode ser `ABERTA`, `EM_ANDAMENTO`, `CONCLUIDA` ou `CANCELADA`
- `fornecedores.cnpj`, `clientes.cpf_cnpj`, `motos_clientes.placa` e
  `motos_clientes.chassi` devem ser **únicos** (marque "Unique" no campo).

## Se quiser automatizar tudo por API no futuro

A criação de tabelas/campos/dados via API (Metadata API) só funciona nos
planos **Essential** ou **Pro** do Xano (confirmado na página oficial de
preços — o Free não libera esse recurso, por isso o token gerado agora não
funcionou). Se decidir fazer upgrade, me avise: com a Metadata API liberada
eu crio as 10 tabelas, os relacionamentos e os dados de exemplo automaticamente
por API, sem precisar de nenhum passo manual.
