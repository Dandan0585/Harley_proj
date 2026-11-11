## 1. Servidor de dados (Xano)

- [x] 1.1 Fazer os endpoints do grupo Admin e o `auth/signup` exigirem o perfil de administrador com `enforce_role`; feito em 24/09/2026 (commit `018aba5`) e verificado em 07/10/2026 no espelho `xano/` (todos chamam `Quick Start/enforce_role`)
- [x] 1.2 Trocar o `throw` da `enforce_role` por `precondition` (resposta 403); feito em 24/09/2026 (commit `510bf61`) e verificado no espelho `xano/function/quick_start/enforce_role.xs`

## 2. Aplicativo

- [x] 2.1 Ler o perfil do `auth/me` e esconder "Usuários do sistema" do menu para quem não é administrador; verificado no código (`AuthState.eh_admin` e `SO_ADMIN` em `layout.py`) e no log da produção de 25/09/2026 (logins com `perfil=member` e `perfil=admin`)
- [x] 2.2 Implementar na tela Usuários criar conta, trocar e-mail, definir senha, mudar perfil e excluir, com as validações de e-mail e senha; verificado no código de `usuarios_state.py` e de `xano_admin_client.py`
- [x] 2.3 Impedir alterar o próprio perfil, excluir a própria conta e excluir a única conta; verificado no código de `usuarios_state.py`
- [x] 2.4 Remover "Criar conta" do login e trocar "Esqueci minha senha" pela orientação de procurar um administrador; verificado no código de `pages/login.py`
- [x] 2.5 Compilar o app; verificado em 07/10/2026 (`reflex compile` sem erros)
