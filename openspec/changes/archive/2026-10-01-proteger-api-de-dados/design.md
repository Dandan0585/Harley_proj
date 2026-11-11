## Context

Motivação em proposal.md. O Xano permite exigir login por endpoint (`auth = "user"`). O app tem uma cópia em memória e uma tarefa de fundo que não pertencem a nenhum funcionário (change `desempenho-e-resiliencia-do-acesso-a-dados`), por isso não podem usar o token de quem está logado. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Nenhum dado acessível sem login.
- Recuperação simples quando a conta de serviço deixar de funcionar.

**Non-Goals:**
- Permissões por perfil nos endpoints de dados (Funcionário e Administrador acessam os mesmos dados).
- Rotação automática de senha.

## Decisions

### D1. Conta de serviço com credenciais no `.env`
`xano_client` faz login com `HARLEY_XANO_EMAIL` e `HARLEY_XANO_SENHA` (lidos do `.env`) e envia o token em toda chamada à API de dados. O token vale 24 horas e é renovado com 20 horas; em uma resposta 401, é renovado e a chamada repetida uma vez.
- *Alternativa:* usar o token do funcionário logado. Rejeitada: a cópia em memória e a tarefa de fundo não têm usuário.

### D2. Espelho do Xano no repositório
As definições do Xano ficam em `xano/`. `scripts/aplicar_xano.ps1` mostra a prévia e pede confirmação antes de gravar, e nunca apaga nada do Xano.

### D3. Script de reparo
`scripts/reparar_conta_servico.py` pede o login de um administrador (senha sem eco), procura a conta de serviço pelo e-mail do `.env`, define uma senha nova (`secrets.token_urlsafe`) pelo endpoint de administração ou cria a conta, grava o `.env` sem mexer nas outras linhas e testa a leitura de clientes.
- *Alternativa:* trocar a senha à mão no painel do Xano e editar o `.env`. Continua possível, mas é mais sujeito a erro.

## Risks / Trade-offs

- [`.env` copiado sem cuidado] → O arquivo está no `.gitignore`; o backup no pendrive o inclui, e isso está avisado no LEIA-ME do backup.
- [Conta de serviço excluída na tela Usuários] → O README avisa para não excluí-la; o script de reparo a recria.
