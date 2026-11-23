## Context

O sistema tem dois perfis vindos do Xano (`role`): `admin` (Administrador) e `member` (Funcionário). O `AuthState` guarda o perfil conferido no Xano (não em cookie) e expõe `eh_admin`. A única tela restrita hoje é "Usuários do sistema": item do menu oculto (`SO_ADMIN` em `components/layout.py`), aviso na tela (`UsuariosState.sem_permissao`) e recusa no Xano.

O `ExigeSessaoMiddleware` (`sessao.py`) roda antes de todo evento dos states protegidos e exige sessão conferida no Xano. Painel, Clientes e Funcionários não olham o perfil. `ClientesState` e `FuncionariosState` não são usados por nenhum outro state: Vendas e OS carregam as próprias listas de clientes e funcionários. O redirecionamento após o login, em `/login` já logado, e o link do logo apontam fixos para `/painel`.

## Goals / Non-Goals

**Goals:**
- Funcionário não vê, não recebe e não altera os dados das quatro telas restritas, com a regra no servidor.
- Todas as telas continuam no menu; o Funcionário vê um aviso claro.
- Funcionário não cai numa tela bloqueada ao entrar no sistema.

**Non-Goals:**
- Restringir outras telas ou criar permissões configuráveis por tela.
- Alterar o Xano.

## Decisions

1. **Recusa no middleware, não em cada handler.** `ExigeSessaoMiddleware` recebe uma segunda lista, `so_admin`, com `DashboardState`, `ClientesState`, `FuncionariosState` e `UsuariosState`. Depois de a sessão ser confirmada, um evento desses states vindo de quem não é administrador é descartado em silêncio (só um log), sem toast, já que a tela mostra o aviso. Assim, todo handler atual e futuro desses states fica coberto. Alternativa descartada: conferir em cada handler, que fica fácil de esquecer num handler novo.
2. **Aviso comum na moldura.** `page(..., so_admin=True)` em `components/layout.py` troca o conteúdo por `aviso_so_admin()` quando `~AuthState.eh_admin`, com o texto "Você precisa ser um administrador para acessar esta tela.". A tela Usuários mantém o `sem_permissao` para o caso de o Xano recusar, usando o mesmo aviso.
3. **Menu:** remover `SO_ADMIN` e o `rx.cond` do menu; todos os itens aparecem para todos.
4. **Tela inicial por perfil:** função pura `tela_inicial_do_perfil(perfil)` em `auth_state.py`, que devolve `/painel` para `admin` e `/vendas` para qualquer outro valor, inclusive vazio. A var `AuthState.tela_inicial` alimenta o `href` do logo, e `fazer_login` e `redirecionar_se_ja_logado` passam a usá-la.

## Risks / Trade-offs

- [O administrador cujo perfil não foi lido no login vê o aviso ou vai para Vendas] → só acontece com o Xano fora do ar; na próxima conferência da sessão o perfil é lido e as telas voltam a funcionar.
- [Dados carregados por um administrador continuam na memória da aba do navegador se, na mesma aba e sem recarregar, um Funcionário entrar em seguida] → a tela mostra só o aviso, e o caso pede o uso compartilhado da mesma aba; fica registrado, sem tratamento nesta change.
- [O Funcionário ainda vê nome e dados básicos do cliente ao escolhê-lo em Vendas e OS] → necessário para o trabalho; fora do escopo.

## Migration Plan

Sem migração de dados. Basta publicar o código; contas `admin` não percebem diferença, exceto o item "Usuários do sistema", que já viam.
