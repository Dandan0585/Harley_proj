## Context

Motivação em proposal.md. Conferido em 07/10/2026:
- nenhum módulo usa `rx.session`, `sqlmodel` ou `alembic`; do `models.py` só são importadas as listas `TIPOS_FUNCIONARIO`, `TIPOS_TRANSACAO` e `STATUS_OS`, em 6 arquivos;
- o `harley_store.db` local tem as tabelas antigas sem registros (auditoria de 01/10/2026) e está fora do git;
- o esquema real do banco está espelhado em `xano/table/*.xs`, e os dados de origem em `xano_import/`;
- a regra `logs/` do `.gitignore` também ignora `xano/api/event_logs/logs/`, que tem o endpoint `logs/user/my_events` do Xano;
- o app de desenvolvimento estava rodando (portas 3000/8000) durante a revisão.

## Goals / Non-Goals

**Goals:**
- Um único caminho documentado para alterar o banco (Xano).
- Nenhuma mudança de comportamento.

**Non-Goals:**
- Refatorar o código das telas (por exemplo, unificar as várias funções de formatar moeda).
- Mudar o Xano ou os dados.
- Juntar as branches `backup_projeto_harley` e `audit/database-refactor`.

## Decisions

### D1. Constantes num módulo próprio
`harley_store/constantes.py` recebe as três listas, com os mesmos nomes e valores; só os imports mudam. O `models.py` sai inteiro, porque suas classes descrevem um banco que o app não usa.
- *Alternativa:* manter o `models.py` só com as constantes. Rejeitada: o nome induz a achar que ali está o esquema do banco.

### D2. Sem banco local
Com `db_url=None` declarado no `rxconfig.py`, o Reflex não verifica nem cria banco local; o app já lê e grava tudo pelo Xano. Só apagar a linha não basta: o padrão do Reflex 0.7.14 é `sqlite:///reflex.db`, e sem a pasta `alembic/` o `reflex run` pararia com "Database is not initialized" (descoberto ao aplicar esta change). O pacote `sqlmodel` continua no `requirements.txt`, porque é dependência do próprio Reflex 0.7.14 (a versão fixada evita a quebra conhecida).

### D3. README como guia de uso
O README ganha um índice e a estrutura real das pastas; o procedimento para alterar o banco passa a ser: propor uma change no OpenSpec, alterar o espelho `xano/`, conferir a prévia com `scripts/aplicar_xano.ps1 -SoPrevia` e aplicar.

### D4. Regra de logs só na raiz
`logs/` vira `/logs/`; as linhas repetidas (`.web`, `.states` e `*.pyc`) saem.

## Risks / Trade-offs

- [Algum script externo usar `reflex db`] → Nenhum script do projeto usa; quem precisar do banco antigo tem o histórico do git e o backup do pendrive.
- [App de desenvolvimento rodando durante a mudança] → O Reflex recarrega sozinho ao salvar os arquivos; a mudança é verificada com `reflex compile` e os testes automáticos, e o usuário reinicia o `reflex run` ao final.

## Migration Plan

Aplicar as tarefas, rodar os testes e o `reflex compile` e pedir ao usuário para reiniciar o `reflex run`. Para voltar atrás, basta reverter o commit da organização.
