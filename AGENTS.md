# AGENTS.md — Instruções para agentes de IA

Regras de trabalho para qualquer agente de IA que atue neste projeto.

## Documentação

- Antes de alterações significativas, ler `docs/project-overview.md`,
  `docs/domain-model.md` e as specs relacionadas em `openspec/specs/`.
- Escrever documentação, artefatos OpenSpec e mensagens da interface em
  português do Brasil.

## Desenvolvimento com OpenSpec

- Toda mudança de comportamento passa pelo ciclo do OpenSpec:
  explore → propose → revisão do grupo → apply → verify → archive.
- Não implementar durante o propose; esperar a aprovação do grupo.
- Se a implementação exigir algo fora do que a change descreve, parar e
  perguntar, em vez de improvisar.

## Frontend

O frontend do projeto deve ser implementado exclusivamente com Reflex.
Utilize os mecanismos próprios do Reflex para componentes, estado, eventos,
páginas e interação. Não introduza outra tecnologia de frontend para
substituir ou complementar o Reflex, salvo quando houver uma alteração
arquitetural explicitamente aprovada.

## Ambiente e Agent Skills do Reflex

- O projeto usa `venv` + `pip` (`.venv` e `requirements.txt`). Não usar
  `uv` nem criar `pyproject.toml`/`uv.lock`, mesmo que o `uv` esteja
  instalado na máquina. Não executar `reflex init` no projeto existente.
- As skills do Reflex (`.agents/skills/`, cópia em `.claude/skills/`)
  complementam estas regras e o OpenSpec, sem substituí-los. Quando
  divergirem, valem as regras deste arquivo:
  - `setup-python-env`: usar sempre o caminho `venv`/`pip`, nunca o do `uv`;
  - `reflex-process-management`: para testar, `reflex compile --dry`; para
    rodar, `reflex run` (ou `scripts/iniciar_dev.ps1`), e não `--env prod`.
    A produção é iniciada só pelos scripts de `scripts/`;
  - `reflex-docs`: a parte de banco (SQLModel) não se aplica, pois os
    dados ficam no Xano.
- Nova biblioteca: confirmar a necessidade, instalar no `.venv`, testar e
  atualizar `requirements.txt` com `pip freeze` na mesma change.

## Arquitetura

- Respeitar a stack definida: Python + Reflex (interface e servidor) e
  Xano (dados e autenticação). Não introduzir outro banco ou framework sem
  justificativa aprovada.
- Cada tela é um par `harley_store/state/<nome>_state.py` +
  `harley_store/pages/<nome>.py`; rotas em `harley_store/harley_store.py`.
- Acesso a dados só por `harley_store/xano_client.py`. O PATCH do Xano
  substitui o registro inteiro: sempre enviar todos os campos.
- Mudanças no banco vão pelo espelho em `xano/` e são aplicadas com
  `scripts/aplicar_xano.ps1`.

## Código

- Reutilizar o código existente e evitar duplicação.
- Não alterar funcionalidades não relacionadas à change atual.
- Escopo enxuto: não criar campos ou tabelas no Xano sem pedido explícito.

## Segurança

- Regras de negócio e de autorização ficam no servidor e no Xano; a
  interface não é mecanismo de segurança.
- Todo state novo deve entrar no `ExigeSessaoMiddleware`.
- Nunca expor ou versionar credenciais (`.env` fica fora do git).
- O Xano é compartilhado entre desenvolvimento e produção: testes com dados
  reais só com registros marcados como TESTE, removidos ao final.

## Testes

- Mudanças funcionais devem ter estratégia de verificação; regras de
  cálculo em funções puras com testes em `tests/`.
- Antes de concluir: `.venv\Scripts\python.exe -m unittest discover -s tests -t .`

## Git

- Commit e envio ao GitHub somente quando o grupo pedir.
