# Proposal

## Why

Hoje o app considera um usuário "logado" apenas porque existe um cookie `hs_auth_token` no navegador: `exigir_login` só confere se o valor não está vazio. O token nunca é conferido com o Xano. Por isso, qualquer valor inventado nesse cookie abre todas as telas, e um token vencido continua valendo no app, já que o Xano emite tokens de 24 horas e o cookie não expira. Com vários funcionários usando o sistema na rede da loja (change `acesso-em-rede-local`), a identidade de quem está logado precisa ser confiável. A change `perfis-de-acesso`, logo depois desta, vai decidir o que cada pessoa pode fazer com base nessa identidade.

Além disso, o id do usuário é guardado num cookie próprio (`hs_auth_user_id_v2`) declarado como número, mas o Reflex trata todo cookie como texto. Isso gera a cada nova sessão o aviso `Expected field 'AuthState.auth_user_id' to receive type 'int', but got '0' of type 'Cookie'`. Trocar o tipo para texto só muda o momento do aviso, porque o valor numérico volta a ser lido como número ao ser reidratado. Esse id também pode ser alterado por quem edita os cookies do navegador.

## What Changes

- O acesso às páginas protegidas passa a exigir um token **aceito pelo Xano**, e não apenas a existência do cookie. Token inválido, vencido ou forjado leva à tela de login.
- A identidade do usuário logado (id, nome, email e perfil) passa a vir do Xano (`auth/me`) a partir do token, e não de valores guardados em cookies.
- O cookie `hs_auth_user_id_v2` deixa de existir (**BREAKING** para as sessões atuais). Resolve o aviso de tipo na raiz e impede que o id seja forjado. Quem estiver logado com um token já vencido precisará entrar de novo.
- O cookie do token passa a expirar junto com o token do Xano, em vez de permanecer indefinidamente.
- Quando o Xano estiver indisponível no momento da validação, o usuário recebe uma mensagem clara, e não é tratado como deslogado nem como logado indevidamente.
- A tela Usuários, que hoje compara o id do cookie para saber se o admin excluiu a própria conta, passa a usar a identidade validada.

Fora do escopo: perfis e permissões (change `perfis-de-acesso`), exigir token nas APIs de dados do Xano (change `proteger-api-de-dados`) e mudanças no fluxo de "esqueci minha senha".

## Capabilities

### New Capabilities
- `plataforma/sessao-de-usuario`: regras da sessão autenticada no app. Cobre o que torna uma sessão válida, a expiração, a origem da identidade do usuário logado, o redirecionamento ao login e o comportamento quando o backend de autenticação está indisponível.

### Modified Capabilities
<!-- Nenhuma: ainda não há specs arquivadas no projeto. A capacidade plataforma/acesso-em-rede-local (change em andamento) não tem requisitos alterados por esta change. -->

## Impact

- **Código**: `harley_store/state/auth_state.py` (validação, remoção de `auth_user_id`, expiração do cookie); `harley_store/xano_auth_client.py` (nova chamada a `auth/me`); `harley_store/state/usuarios_state.py` (identidade do usuário logado); `harley_store/components/layout.py` (nome exibido no menu).
- **APIs Xano**: passa a usar `GET auth/me` do grupo Authentication, que já existe e exige token. Nenhum endpoint novo e nenhuma mudança de schema.
- **Desempenho / limites**: cada validação é uma chamada ao Xano, e o `auth/me` atual grava um registro em `event_log` a cada chamada. A frequência da validação (a cada página ou uma vez por sessão, com revalidação) precisa ser decidida no design, por causa do limite de requisições do plano Free e do crescimento do `event_log`.
- **Usuários**: sessões com token vencido serão encerradas no primeiro acesso após a mudança.
- **Dependências**: nenhuma nova.
- **Relação com outras changes**: depende de `acesso-em-rede-local`, que coloca vários usuários na rede; é pré-requisito de `perfis-de-acesso`, que usará o `role` retornado pelo `auth/me`.
