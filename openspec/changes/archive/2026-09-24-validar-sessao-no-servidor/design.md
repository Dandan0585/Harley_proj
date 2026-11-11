## Context

Motivação em proposal.md. Esta change foi implementada na auditoria de 24/09/2026 (commit `018aba5`), antes de existirem a especificação, o desenho e as tarefas; os artefatos foram completados em 07/10/2026 a partir do código, para registrar o que de fato está em produção.

Restrições que moldaram a solução:
- o Xano emite tokens de 24 horas e oferece `GET auth/me` (grupo Authentication), que exige o token e devolve id, nome, e-mail e perfil;
- cada chamada a `auth/me` conta no limite de requisições do plano Free e grava um registro em `event_log`;
- no Reflex, qualquer evento de um state pode ser enviado direto pelo websocket, sem abrir a página.

## Goals / Non-Goals

**Goals:**
- Sessão confiável com o menor número possível de chamadas ao Xano.
- Proteção no servidor, não só na abertura das páginas.

**Non-Goals:**
- Perfis e permissões (change `perfis-de-acesso`).
- Login obrigatório na API de dados (change `proteger-api-de-dados`).

## Decisions

### D1. Conferência com `auth/me` e revalidação a cada 10 minutos
`AuthState.validar_sessao()` confere o token no Xano e guarda, só no servidor, qual token foi conferido e quando. Dentro de 10 minutos (`REVALIDAR_SEGUNDOS = 600`) o mesmo token não é conferido de novo.
- *Alternativa:* conferir a cada página ou ação. Rejeitada: multiplicaria as requisições ao Xano Free e os registros em `event_log`.
- *Custo aceito:* uma conta excluída mantém o acesso por até 10 minutos.

### D2. Identidade fora dos cookies
Ficam em cookie só o token (`hs_auth_token`) e o nome para exibição (`hs_usuario`), ambos com validade de 24 horas. O id e o perfil ficam em variáveis do state preenchidas pelo `auth/me`. O cookie `hs_auth_user_id_v2` foi removido, o que também acabou com o aviso de tipo do Reflex na raiz.

### D3. Middleware que exige sessão
`sessao.ExigeSessaoMiddleware` roda antes de todo evento. Para os states listados em `harley_store.py` (todos os do app, menos o `AuthState`), chama `validar_sessao()`; sem sessão, devolve o evento `AuthState.sessao_expirada` (aviso + login) e o evento original não roda. Toda página protegida também tem `AuthState.exigir_login` como primeiro item do `on_load`.

### D4. Xano fora do ar
`xano_auth_client.me()` diferencia "token recusado" (401/403, exceção `SessaoInvalida`) de erro de rede ou do servidor. No segundo caso, quem já foi conferido nesta sessão continua trabalhando; quem ainda não foi recebe uma mensagem de falta de conexão.

## Risks / Trade-offs

- [Janela de 10 minutos após excluir uma conta] → Aceita pelo custo de requisições; o administrador pode trocar a senha da conta, o que não encurta a janela, mas impede novos logins.
- [State novo fora da lista do middleware] → O comentário em `harley_store.py` avisa que todo state novo precisa entrar na lista de `ExigeSessaoMiddleware`.
