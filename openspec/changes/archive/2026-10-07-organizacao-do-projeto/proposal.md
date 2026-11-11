## Why

O projeto passou por três bancos (SQL Server, SQLite local e Xano) e ainda carrega restos das fases antigas: o `rxconfig.py` aponta para um banco SQLite que nada usa, o `models.py` tem 10 tabelas SQLModel sem uso e a pasta `alembic/` tem migrações desse banco. O README orienta a alterar o banco por esse caminho antigo, que não funciona mais. Na revisão de 07/10/2026 também apareceram um caractere invisível corrompendo um comando do README e uma regra do `.gitignore` que deixava um endpoint do espelho do Xano fora do controle de versão.

## What Changes

- README: correção do comando corrompido, índice no topo, estrutura do projeto atualizada, procedimento correto para alterar o banco (Xano) e seção do OpenSpec atualizada; sai a seção sobre conectar no SQL Server.
- Remoção do legado do SQLite: `db_url` do `rxconfig.py`, tabelas SQLModel do `models.py`, pasta `alembic/`, `alembic.ini` e o arquivo local `harley_store.db`; as três listas de constantes ainda usadas pelas telas passam para `harley_store/constantes.py`.
- `.gitignore`: a regra de logs passa a valer só para a pasta `logs/` da raiz (o endpoint `xano/api/event_logs/logs/` volta ao controle de versão) e saem as linhas repetidas.
- `openspec/config.yaml`: contexto atualizado (especificações organizadas por domínio, dados só no Xano).
- Git: remoção da branch local `backup/antes-de-voltar-23-09`, cujo conteúdo já está na `backup_projeto_harley` e no backup do pendrive.

Nenhuma tela, regra de negócio ou dado muda.

## Capabilities

### New Capabilities
<!-- Nenhuma: organização sem mudança de comportamento (skip_specs). -->

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `rxconfig.py`, `harley_store/models.py` (removido), novo `harley_store/constantes.py` e 6 imports em `pages/` e `state/` (funcionários, ordens de serviço e vendas).
- **Arquivos removidos**: `alembic/`, `alembic.ini`, `harley_store.db` (local, fora do git).
- **Documentação**: `README.md`, `.gitignore`, `openspec/config.yaml`.
- **Dados (Xano)**: nenhuma mudança.
- **Recuperação**: tudo o que sai continua no histórico do git e no backup do pendrive de 01/10/2026.
