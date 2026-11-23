## Why

Hoje as telas Painel, Clientes e Funcionários só exigem login: qualquer conta com o perfil Funcionário vê o faturamento e o estoque da loja, os dados pessoais dos clientes e o cadastro da equipe, e ainda pode alterar ou excluir esses cadastros, exatamente como o Administrador. Isso tira o sentido da separação de perfis. Além disso, o Painel é a tela para onde todos vão depois do login e ao clicar no logo, então o Funcionário cai nele sempre.

## What Changes

- **Telas só para administradores:** Painel, Clientes, Funcionários e Usuários do sistema.
  - Todas as telas continuam no menu para todos os perfis. O item "Usuários do sistema", que hoje fica oculto para o Funcionário, passa a aparecer também.
  - Quem não é administrador e abre uma dessas telas vê o aviso **"Você precisa ser um administrador para acessar esta tela."**, sem nenhum dado.
  - A regra vale no servidor: o `ExigeSessaoMiddleware` passa a recusar qualquer evento dos states dessas telas (carregar, salvar, excluir, buscar...) vindo de quem não é administrador, mesmo que o evento seja chamado direto pelo websocket.
- **Tela inicial por perfil:** depois do login, ao abrir `/login` já logado e ao clicar no logo do menu, o Administrador vai para o Painel e o Funcionário vai para **Vendas / Balcão** (`/vendas`).
- **Documentação:** `docs/project-overview.md` deixa de dizer que o Funcionário consulta o painel e mantém cadastros de clientes; `README.md` registra a restrição.

**Fora do escopo:**
- restringir outras telas (Produtos, Motos dos clientes, Vendas, OS, Compras, Fornecedores);
- a escolha do cliente e do funcionário dentro de Vendas e OS, que continua funcionando para o Funcionário (essas telas carregam as próprias listas);
- criar novos perfis ou mudar os perfis existentes (`admin` e `member`) no Xano;
- mudar os cálculos do Painel ou os campos dos cadastros;
- mudanças no Xano: os dados são lidos pela conta de serviço do servidor, então a regra fica no servidor do Reflex.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `plataforma/perfis-de-acesso`: novo requisito "Telas só para administradores" (Painel, Clientes, Funcionários e Usuários), novo requisito "Tela inicial por perfil", e o requisito "Administração de contas só para administradores" deixa de ocultar o item do menu.

## Impact

- Código: `harley_store/sessao.py` (recusa dos eventos das telas restritas), `harley_store/harley_store.py` (lista de states restritos), `harley_store/components/layout.py` (aviso comum, menu e destino do logo), `harley_store/state/auth_state.py` (tela inicial por perfil), `harley_store/pages/dashboard.py`, `clientes.py`, `funcionarios.py` e `usuarios.py` (aviso); testes em `tests/`.
- Xano: nenhuma alteração.
- Documentação: `README.md`, `docs/project-overview.md`.
