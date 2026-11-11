## Why

Qualquer pessoa podia criar uma conta pela tela de login ou trocar a senha de qualquer conta sabendo só o e-mail, e todas as contas podiam gerir as demais. Com vários funcionários usando o sistema, era preciso separar quem administra as contas de quem só opera a loja. A change `validar-sessao-no-servidor` já citava esta change como a próxima.

Registro retroativo: implementado na auditoria de 24/09/2026 (commit `018aba5`), com o ajuste da recusa com o status correto em `510bf61`. Esta change documenta o comportamento em uso.

## What Changes

- Dois perfis de acesso: Administrador e Funcionário. Contas novas são criadas como Funcionário.
- A tela "Usuários do sistema" passa a ser só de administradores: o item some do menu dos demais, e o servidor de dados recusa as operações de quem não é administrador.
- O administrador cria contas, troca e-mails, define uma nova senha, muda o perfil e exclui contas, com proteções contra se trancar fora do sistema.
- **BREAKING**: deixam de existir o cadastro público ("Criar conta") e a troca de senha sem confirmação; "Esqueci minha senha" orienta a pedir a um administrador.

## Capabilities

### New Capabilities
- `plataforma/perfis-de-acesso`: perfis de acesso e administração das contas de login.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/state/usuarios_state.py`, `harley_store/pages/usuarios.py`, `harley_store/xano_admin_client.py`, `harley_store/state/auth_state.py` (perfil), `harley_store/pages/login.py` e `harley_store/components/layout.py` (menu).
- **Xano**: endpoints do grupo Admin (`user/list`, `user/set-password`, `user/set-role`, `user/update-email`, `user/delete`) e `auth/signup` conferindo o perfil com a função `Quick Start/enforce_role`.
- **Usuários**: contas novas só são criadas por um administrador.
