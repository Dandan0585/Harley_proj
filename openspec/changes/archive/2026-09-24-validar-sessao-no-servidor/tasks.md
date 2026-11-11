## 1. Conferência da sessão

- [x] 1.1 Criar `xano_auth_client.me(token)`, que chama `GET auth/me` e diferencia token recusado (`SessaoInvalida`) de falha de conexão; verificado no código (commit `018aba5`, 24/09/2026)
- [x] 1.2 Implementar `AuthState.validar_sessao()` com revalidação a cada 10 minutos e os três resultados (ok, inválida, indisponível); verificado no log da produção de 25/09/2026, que registra o perfil vindo do `auth/me` em cada login (`login usuario_id=13 perfil=member`)
- [x] 1.3 Fazer `exigir_login` usar a conferência e redirecionar ao login só quando o token for recusado; verificado em 07/10/2026: todas as 11 páginas protegidas em `harley_store.py` têm `AuthState.exigir_login` como primeiro item do `on_load`

## 2. Identidade e cookies

- [x] 2.1 Remover o cookie `hs_auth_user_id_v2` e guardar id e perfil só no servidor; verificado em 07/10/2026: não há mais nenhuma referência ao cookie no código
- [x] 2.2 Fazer os cookies `hs_auth_token` e `hs_usuario` vencerem em 24 horas, junto com o token; verificado no código (`max_age = 86400`)
- [x] 2.3 Fazer a tela Usuários usar a identidade conferida (impedir excluir a própria conta e alterar o próprio perfil); verificado no código de `usuarios_state.py`

## 3. Proteção no servidor

- [x] 3.1 Criar `sessao.ExigeSessaoMiddleware` e registrá-lo com todos os states do app, menos o `AuthState`; verificado em 07/10/2026: os 12 states estão na lista do middleware em `harley_store.py`
- [x] 3.2 Tratar o Xano fora do ar sem deslogar quem já foi conferido; verificado no código (`validar_sessao` devolve ok para token já conferido e "indisponível" para token ainda não conferido)
- [x] 3.3 Compilar o app e rodar os testes automáticos; verificado em 07/10/2026 (`reflex compile` sem erros e testes passando)
