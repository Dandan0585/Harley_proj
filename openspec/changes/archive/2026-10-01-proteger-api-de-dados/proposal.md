## Why

A API de dados do Xano respondia sem login: qualquer pessoa com o endereço podia ler, alterar ou apagar clientes, CPFs e vendas. A change `validar-sessao-no-servidor` deixou isso fora do escopo e citava esta change como a responsável.

Registro retroativo: implementado na auditoria de 24/09/2026 (commit `018aba5`); o script de reparo da conta de serviço foi criado em 01/10/2026 (commit `cb9b8ff`), depois que a senha dessa conta passou a ser recusada. Esta change documenta o comportamento em uso.

## What Changes

- Todos os endpoints de dados passam a exigir login.
- O servidor do app acessa os dados com uma conta de serviço própria, cujas credenciais ficam no arquivo `.env`, fora do controle de versão.
- O token da conta de serviço é renovado antes de vencer e, se recusado, renovado e a chamada repetida.
- Novo procedimento para reparar a conta de serviço (senha nova, gravada no Xano e no `.env`), feito por um administrador.

## Capabilities

### New Capabilities
- `plataforma/protecao-da-api-de-dados`: acesso autenticado à API de dados e gestão da conta de serviço do app.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Xano**: 74 endpoints do grupo HARLEY com `auth = "user"`; espelho em `xano/` aplicado com `scripts/aplicar_xano.ps1` (prévia e confirmação).
- **Código**: `harley_store/xano_client.py` (login da conta de serviço e renovação do token) e `scripts/reparar_conta_servico.py`.
- **Operação**: cada pasta do app (desenvolvimento e produção) precisa do `.env` com `HARLEY_XANO_EMAIL` e `HARLEY_XANO_SENHA`.
