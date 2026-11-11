## Context

Motivação em proposal.md. As contas ficam na tabela `user` do Xano, que já tem o campo `role` e a função `Quick Start/enforce_role` (hierarquia admin > member). A identidade e o perfil de quem está logado vêm do `auth/me` (change `validar-sessao-no-servidor`). Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Regra aplicada no servidor de dados, não só na tela.

**Non-Goals:**
- Permissões por tela para o perfil Funcionário (todas as telas de operação continuam liberadas).
- Recuperação de senha por e-mail.

## Decisions

### D1. Regra no Xano, com o token de quem está logado
`xano_admin_client` chama o grupo Admin com o token do administrador logado, e cada endpoint chama `enforce_role` com `required_role = "admin"`. A função usa `precondition`, que responde 403; antes ela usava `throw`, que o Xano devolvia como 200 com o erro no corpo, e o app passou a reconhecer os dois formatos como "sem permissão".
- *Alternativa:* conferir o perfil só no app. Rejeitada: a API poderia ser chamada diretamente.

### D2. Tela só esconde o que a pessoa não pode usar
O menu usa `AuthState.eh_admin` para esconder "Usuários do sistema", e `UsuariosState` não chama o Xano sem perfil de administrador. A proteção real é o Xano (D1).

### D3. Fim do autoatendimento
`auth/signup` passou a exigir um administrador. Os endpoints de redefinição de senha por código também conferem o perfil, e a aba "Esqueci minha senha" só orienta a procurar um administrador.

## Risks / Trade-offs

- [Administrador esquece a própria senha] → Outro administrador redefine; se não houver, a senha precisa ser trocada no painel do Xano.
- [Exclusão da conta de serviço do app] → A tela não bloqueia; o README avisa para não excluir a conta "Sistema Harley Store", e o script `reparar_conta_servico.py` a recria (change `proteger-api-de-dados`).
