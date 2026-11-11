## 1. README

- [x] 1.1 Corrigir o comando `.\scripts\atualizar_producao.ps1`, que tinha um caractere invisível (BEL) no lugar de `\a` desde o commit `44eb620`; corrigido na revisão de 07/10/2026 e verificado pela varredura de caracteres de controle em todos os arquivos de texto do projeto (nenhum restante)
- [x] 1.2 Acrescentar um índice no topo do README; verificar que cada link do índice aponta para uma seção existente (feito em 07/10/2026; verificado: os 16 links internos do README apontam para títulos existentes, pela regra de âncoras do GitHub. O título "Modo demonstração (atual)" foi encurtado para a âncora ficar estável)
- [x] 1.3 Reescrever "Estrutura do projeto" com as pastas e arquivos reais (`scripts/`, `tests/`, `openspec/`, `xano/`, `assets/motos/`, módulos novos); verificar que cada caminho citado existe (verificado em 07/10/2026: os 27 itens da árvore existem)
- [x] 1.4 Trocar "Como alterar a estrutura do banco" pelo procedimento do Xano (change no OpenSpec, espelho `xano/`, prévia e aplicação) e remover "Como conectar no SQL Server"; verificar que não sobra menção a `reflex db`, `alembic` ou `models.py` como forma de alterar o banco (verificado em 07/10/2026: não sobra instrução com `reflex db`, `alembic`, `models.py` ou SQL Server; as únicas menções estão na seção Backup e informam que o legado foi removido. Para cumprir essa verificação também foram corrigidos o passo 5 de "Como rodar", que mandava rodar `reflex db init`/`migrate` e agora orienta copiar o `.env`, e o parágrafo da seção Backup. Ajustes pequenos feitos junto: pasta do projeto no passo 1, descrição do cache em Desempenho e a linha solta `# LOJA-EXTRA-HARLEY` no fim do arquivo)
- [x] 1.5 Atualizar a seção "OpenSpec" (especificações por domínio, changes arquivadas, a change aberta e o fluxo propor, aplicar e arquivar); verificar com `openspec list` e `openspec list --specs` (verificado em 07/10/2026 com `openspec list` e `openspec list --specs`: 1 change aberta além desta e 17 especificações em 11 domínios)

## 2. Legado do SQLite

- [x] 2.1 Criar `harley_store/constantes.py` com `TIPOS_FUNCIONARIO`, `TIPOS_TRANSACAO` e `STATUS_OS` e trocar os 6 imports; verificar com `grep` que nada importa mais `models`
- [x] 2.2 Remover `harley_store/models.py`, a pasta `alembic/`, o `alembic.ini` e o `db_url` do `rxconfig.py`; verificar com `reflex compile` sem erros (feito em 07/10/2026 com `db_url=None` explícito; verificado com `reflex compile` e com as checagens de banco que o `reflex run` faz ao iniciar: `check_db_initialized` e `check_schema_up_to_date` passam)
- [x] 2.3 Remover o arquivo local `harley_store.db` e atualizar os comentários do `requirements.txt` sobre SQL Server; verificar que o arquivo não é citado em mais nenhum lugar (feito em 07/10/2026; a cópia de 01/10/2026 está no backup do pendrive. Restam só citações históricas: o README, reescrito na tarefa 1.4, e o desenho da change aberta `acesso-em-rede-local`, que explica a regra `*.db` do `.gitignore`)

## 3. Configuração e git

- [x] 3.1 Corrigir o `.gitignore` (`/logs/` só na raiz e sem linhas repetidas); verificar que `git status` passa a mostrar `xano/api/event_logs/logs/user/my_events_GET.xs` e continua ignorando `logs/`, `.env`, `.web/` e `.venv/` (verificado em 07/10/2026 com `git status` e `git check-ignore` em 12 caminhos)
- [x] 3.2 Atualizar o contexto em `openspec/config.yaml`; verificar com `openspec validate --all --strict` (verificado em 07/10/2026: 19 itens válidos)
- [x] 3.3 Remover a branch local `backup/antes-de-voltar-23-09`; verificar antes, com `git diff`, que ela não tem nenhum arquivo que falte na `backup_projeto_harley` (verificado em 07/10/2026: nenhum arquivo exclusivo, e o conteúdo é o do commit `cb9b8ff`, já contido na `backup_projeto_harley`, menos o script de reparo, a correção do menu "Produtos" (3 linhas em `produtos_state.py`) e 12 linhas do README, acrescentadas depois; o commit `8f741ae` continua no `.git` copiado para o pendrive)

## 4. Verificação

- [x] 4.1 Rodar os testes automáticos e o `reflex compile`; verificar que todos os testes passam e a compilação não tem erros (verificado em 07/10/2026: 44 testes passando, `reflex compile` sem erros, nenhum caractere de controle nos arquivos de texto, 19 itens válidos no `openspec validate --all --strict` e o app de desenvolvimento aberto continuou respondendo, com backend e tela em HTTP 200)
