## 1. Servidor de dados (Xano)

- [x] 1.1 Exigir login (`auth = "user"`) em todos os endpoints de dados e aplicar com `scripts/aplicar_xano.ps1`; feito em 24/09/2026 (commit `018aba5`) e verificado em 07/10/2026: os 74 endpoints do grupo HARLEY no espelho têm `auth = "user"`, e as listas de clientes, produtos e vendas respondem 401 sem login

## 2. Conta de serviço

- [x] 2.1 Fazer o `xano_client` entrar com a conta de serviço do `.env`, renovar o token com 20 horas e repetir a chamada uma vez após 401; verificado no código e no log da produção (`token da conta de servico obtido` a cada subida)
- [x] 2.2 Registrar no log a falta das credenciais; verificado no código (`HARLEY_XANO_EMAIL/HARLEY_XANO_SENHA ausentes no .env`)
- [x] 2.3 Documentar o `.env` no README (seção "Segurança da API do Xano e conta de serviço"); verificado em 07/10/2026

## 3. Reparo

- [x] 3.1 Criar `scripts/reparar_conta_servico.py` (login de administrador, senha nova sem exibir, `.env` do desenvolvimento e, com confirmação, da produção, teste de leitura); feito em 01/10/2026 (commit `cb9b8ff`) e verificado pelo usuário, que confirmou o sistema funcionando depois do reparo
- [x] 3.2 Documentar o reparo no README; verificado em 07/10/2026
