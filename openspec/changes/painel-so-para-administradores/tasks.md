## 1. Regras no servidor

- [x] 1.1 Em `auth_state.py`, criar a função pura `tela_inicial_do_perfil(perfil)` (`/painel` para `admin`, `/vendas` para os demais, inclusive vazio) e a var `AuthState.tela_inicial`; usar em `fazer_login` e `redirecionar_se_ja_logado`; verificar com teste automático (admin, member e vazio) (`tests/test_perfis_de_acesso.py`)
- [x] 1.2 Em `sessao.py`, aceitar a lista `so_admin` e descartar os eventos desses states vindos de quem não é administrador; em `harley_store.py`, passar `DashboardState`, `ClientesState`, `FuncionariosState` e `UsuariosState`; verificar com teste automático (evento de member recusado, de admin aceito, de state não restrito aceito) (`tests/test_perfis_de_acesso.py`: member recusado em carregar, salvar e excluir; perfil não conferido recusado; admin aceito; Vendas aceita)

## 2. Interface

- [x] 2.1 Em `components/layout.py`, criar `aviso_so_admin()` e o parâmetro `so_admin` em `page`; remover `SO_ADMIN` do menu; trocar o `href` do logo por `AuthState.tela_inicial`
- [x] 2.2 Usar `so_admin=True` em `pages/dashboard.py`, `clientes.py`, `funcionarios.py` e `usuarios.py` (nesta, o aviso de `sem_permissao` passa a ser o comum)

## 3. Verificação e documentação

- [x] 3.1 Rodar `.venv\Scripts\python.exe -m unittest discover -s tests -t .` e `reflex compile --dry`; verificar que passam (23/11/2026: 106 testes OK, 6 novos; "App compiled successfully")
- [ ] 3.2 Conferir no app com uma conta Funcionário marcada como TESTE (vai para Vendas ao entrar, todos os itens no menu, aviso nas quatro telas, Vendas e OS ainda escolhem cliente e funcionário) e com uma conta Administrador (telas normais); remover a conta TESTE ao final
- [x] 3.3 Atualizar `README.md` e `docs/project-overview.md` (papéis do Administrador e do Funcionário); verificar lendo as seções
