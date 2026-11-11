# Harley Store App

Aplicativo web para o dia a dia da loja/oficina, construído em [Reflex](https://reflex.dev)
(Python puro — sem precisar escrever HTML/JS) a partir da estrutura do banco
`HARLEY_DAVIDSON_STORE.sql` que você enviou.

Ele cobre as 10 tabelas do banco original: Fornecedores, Produtos, Funcionários,
Clientes, Motos dos Clientes, Entrada de Mercadoria (Compras), Itens de Compra,
Transações (Vendas), Ordens de Serviço e Itens de Ordem de Serviço.

## Índice

- [O que o app faz](#o-que-o-app-faz)
- [Como rodar (no VSCode)](#como-rodar-no-vscode)
- [Modo demonstração (atual)](#modo-demonstração-atual)
- [Produção e desenvolvimento (rede da loja)](#produção-e-desenvolvimento-rede-da-loja)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Regras de integridade (estoque, cadastros e sessão)](#regras-de-integridade-estoque-cadastros-e-sessão)
- [Testes automáticos](#testes-automáticos)
- [Contas, perfis e senhas](#contas-perfis-e-senhas)
- [Segurança da API do Xano e conta de serviço](#segurança-da-api-do-xano-e-conta-de-serviço)
- [Spinner de carregamento nos botões](#spinner-de-carregamento-nos-botões)
- [Fotos](#fotos)
- [E-mails automáticos (SendGrid)](#e-mails-automáticos-sendgrid)
- [Pagamentos pelo Asaas](#pagamentos-pelo-asaas)
- [Histórico de estoque](#histórico-de-estoque)
- [OpenSpec](#openspec)
- [Backup](#backup)

## O que o app faz

- **Tela inicial** (`/`) — logo Harley-Davidson sobre fundo preto, com o
  botão **ENTRAR** que leva ao login (`/login`). Depois do login o usuário
  vai para o Painel (`/painel`). O logo fica em `assets/harley_logo.png`
  e as cores da marca em `harley_store/components/tema.py`.
- **Painel** (`/painel`) — visual Harley (preto + laranja): motos em
  estoque, **Estoque de Motos** (preço de compra) e **Estoque de Produtos**
  (quantidade × preço de venda), motos vendidas no mês, faturamento de
  hoje e **Faturamento de Motos / de Produtos** do mês, gráfico de
  faturamento dos últimos 12 meses (motos + produtos, com o total do dia e
  do mês), produtos, estoque baixo, clientes, OS em aberto e um extrato
  recente (igual à view `vw_resumo_operacoes` do script original, só que
  calculada em Python). O faturamento soma os produtos e a mão de obra das
  vendas e as **OS concluídas** (peças + mão de obra), no dia em que a OS
  foi marcada como Concluída; não inclui vendas canceladas nem compras. Dia
  e mês seguem o fuso de São Paulo. As regras ficam no topo de
  `harley_store/state/dashboard_state.py`.
- **Produtos** — catálogo e estoque, separado em **abas por categoria**
  (com a quantidade de cada uma), aviso de estoque baixo (≤ 5 unidades),
  busca e categorias sugeridas (Peças, Vestuário, Consumíveis, Acessórios,
  Motores, Pneus, Lubrificantes, Outros). Uma categoria nova é só
  digitada: não precisa mudar código. Ao escolher uma categoria, o
  cadastro de produto novo já vem com ela preenchida.
- **Produtos > aba Motos** (`/produtos?aba=motos`; o antigo `/motos-loja`
  leva para lá) — o estoque de motos à venda, que antes era a página Motos
  da loja. Na aba Motos o formulário vira o de moto, ligado à tabela
  `motos` do Xano: marca, modelo, ano, cor, placa, chassi, km, RENAVAM,
  cilindrada, localização, situação (Em estoque, Em preparação, Em
  manutenção, Reservada, Consignada, Indisponível, Vendida), preços de
  compra e venda, datas de entrada/saída, cliente, observações e fotos
  (principal + até 8 adicionais, com galeria ampliada). Só "Vendida" tira
  a moto do estoque, e ela exige o cliente comprador e o chassi. Moto sem
  foto enviada mostra a **foto oficial** do modelo.
- **Clientes** e **Motos dos clientes** — cadastro e vínculo cliente → moto.
  As motos dos clientes mostram a foto oficial do modelo cadastrado.
  Cliente cadastrado com e-mail recebe um **e-mail de boas-vindas**, e quem
  compra uma moto da loja recebe um **e-mail de parabéns** (ver "E-mails
  aos clientes (SendGrid)").
- **Vendas / Balcão** — venda com **vários itens** (carrinho): produtos do
  estoque (preço já preenchido e editável, para descontos) e itens avulsos
  sem estoque (ex.: mão de obra). O estoque é baixado na hora, protegido
  contra vendas simultâneas do mesmo produto. Vendas **não são apagadas**:
  são **canceladas** (uma ou várias de uma vez, com motivo opcional),
  continuam no histórico como "Cancelada", saem do faturamento e devolvem
  os produtos ao estoque. O **tipo** da venda é BALCAO, PECAS ou MOTO
  (MOTO = venda ligada a uma moto; peças e serviços contam em Produtos no
  Painel). Compras ficam na tela Compras; os tipos antigos COMPRA e
  ORDEM_SERVICO só aparecem em vendas registradas antes de 09/10/2026.
  **Moto da loja no Balcão:** a tela lista as motos disponíveis (todas,
  menos Vendida e Indisponível) com foto, preço de venda, placa, chassi,
  RENAVAM e demais dados. A moto entra pelo preço do cadastro (uma por
  venda, com cliente obrigatório e junto com acessórios, se quiser). Ao
  registrar, a moto fica **Vendida**, conta uma vez em Motos no Painel, é
  cadastrada em **Motos dos clientes** em nome do comprador (moto sem placa
  fica para depois do emplacamento) e o cliente recebe o e-mail de
  parabéns. Cancelar a venda devolve a moto ao estoque. Isso exige o campo
  `moto_id` em `itens_transacao` no Xano (`scripts\aplicar_xano.ps1`);
  sem ele, a venda de moto é recusada sem alterar nada. A moto também pode
  ser vendida pelo próprio cadastro em Produtos > Motos.
  **Forma de pagamento:** ao concluir a venda, o funcionário escolhe Na
  loja, Boleto, Cartão de crédito ou Cliente escolhe. As três últimas geram
  a cobrança no **Asaas**, que a envia ao cliente por e-mail e SMS; a lista
  mostra a situação do pagamento e o link da cobrança, e o cliente recebe
  um e-mail de confirmação quando paga (ver [Pagamentos pelo
  Asaas](#pagamentos-pelo-asaas)).
- **Ordens de serviço** — abre OS vinculada a uma moto e um mecânico, permite
  lançar peças usadas (que também baixam o estoque) e serviços / mão de
  obra (descrição e valor, sem estoque), e trocar o status
  (Aberta → Em andamento → Concluída/Cancelada). Excluir uma OS devolve
  as peças ao estoque.
- **Compras** — dá entrada de mercadoria de um fornecedor com vários itens
  de uma vez; cada item já soma no estoque do produto correspondente. A
  coluna **Descrição** mostra o que foi pedido ao fornecedor: começa com os
  itens da compra e pode ser reescrita pelo lápis ao lado.
  Excluir uma compra retira do estoque o que ela somou (e é recusado se
  esses produtos já foram vendidos).
- **Fornecedores** e **Funcionários** — cadastros de apoio.
- **Impressão de documentos** — botão **Imprimir** em Vendas, Ordens de
  serviço, Compras e Produtos > Motos. Abre em nova aba uma folha A4
  (comprovante de venda, ordem de serviço, entrada de mercadoria, recibo de
  compra e venda ou ficha da moto) com cliente/fornecedor, itens, total e
  assinaturas; imprime ou salva em PDF pelo navegador.

### Desempenho

O servidor guarda as tabelas do Xano em cache (5 min) e as mantém
atualizadas em segundo plano (1 consulta a cada 20 s), então as telas abrem
em cerca de 0,1–0,9 s e o limite de requisições do plano Free do Xano não é
atingido. Toda gravação feita pelo app atualiza a cópia em memória na hora,
sem reler a tabela; uma alteração feita direto no painel do Xano aparece no
app em até 5 minutos.

## Como rodar (no VSCode)

Pré-requisitos: **Python 3.11, 3.12 ou 3.13** instalado (⚠️ **não use Python
3.14** — o Reflex ainda não é compatível com ele; a instalação quebra com
`ImportError: cannot import name 'Discriminator' from 'pydantic.v1'` ou
`RuntimeError: generator didn't stop after throw()`, ver
[reflex-dev/reflex#5964](https://github.com/reflex-dev/reflex/issues/5964)),
e a extensão **Python** do VSCode (o Reflex também baixa sozinho, na primeira
execução, um runtime Node.js/Bun próprio para compilar a interface — você
não precisa instalar Node manualmente).

Para conferir quais versões de Python você tem instaladas no Windows, rode
`py -0` no terminal. Se só aparecer a 3.14, baixe o instalador do Python 3.12
em python.org, marque "Add python.exe to PATH" na instalação, e use `py
-3.12` no lugar de `python` nos comandos abaixo.

1. Abra a pasta do projeto (`C:\LOJA-EXTRA-HARLEY`) no VSCode: `Arquivo → Abrir Pasta...`.
2. Abra um terminal no VSCode (`Terminal → Novo Terminal`) e crie um ambiente
   virtual **com uma versão suportada do Python**:

   ```bash
   # Windows (troque -3.12 por -3.11 ou -3.13 se for a versão que você tem):
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   # macOS/Linux:
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Atualize o `pip` e instale as dependências (o Reflex já está na lista):

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   reflex --version
   ```

   **Não rode `reflex init`:** ele serve só para criar um projeto novo. Na
   primeira execução, o `reflex run` prepara sozinho os arquivos do frontend.

4. No VS Code, escolha o Python do `.venv` (Ctrl+Shift+P → **Python: Select
   Interpreter** → o que está em `.venv`).

5. Copie para a pasta o arquivo `.env` de uma instalação existente (tem a
   conta de serviço do Xano e, se configurados, o SendGrid e o Asaas; veja
   [Segurança da API do Xano e conta de serviço](#segurança-da-api-do-xano-e-conta-de-serviço)).
   Não há banco local: todos os dados ficam no Xano.

6. Rode o app de **desenvolvimento** e acesse **http://localhost:3001**:

   ```powershell
   .\scripts\iniciar_dev.ps1
   ```

   O sistema que os funcionários usam é a **produção**, que roda sozinha;
   veja a seção abaixo.

## Modo demonstração (atual)

Só `reflex run`, neste computador.

Hoje o sistema **não sobe sozinho** e não fica na rede da loja: roda só
quando você manda, em http://localhost:3000.

1. Abra a pasta `C:\LOJA-EXTRA-HARLEY` no VSCode.
2. Abra um terminal (`Terminal → Novo Terminal`): ele já abre com `(.venv)`.
3. Rode `reflex run` e acesse **http://localhost:3000** (ou `Ctrl+Shift+B`).
4. Para parar: `Ctrl+C` no terminal.

Precisa de internet (os dados estão no Xano) e do arquivo `.env` na pasta.

Para voltar a ser o servidor da loja (como administrador): reative a
tarefa com `Enable-ScheduledTask -TaskName HarleyStore-Producao`, fixe o IP
com `.\scripts\ip_do_servidor.ps1 -Fixo` e ligue a produção com
`Start-ScheduledTask -TaskName HarleyStore-Producao`. A seção abaixo
descreve esse modo.

## Produção e desenvolvimento (rede da loja)

O mesmo notebook roda dois ambientes, em pastas separadas:

| | Produção (funcionários) | Desenvolvimento |
|---|---|---|
| Endereço | **http://192.168.0.12:3000**, em qualquer aparelho da rede da loja | http://localhost:3001, só neste notebook |
| Pasta | `C:\HARLEY_PROD` (clone git, **não edite arquivos lá**) | `C:\LOJA-EXTRA-HARLEY` |
| Portas | 3000 (tela) / 8000 (backend), liberadas no firewall só na rede Privada | 3001 / 8001, fechadas para a rede |
| Como sobe | sozinha quando o notebook liga (tarefa agendada `HarleyStore-Producao`) | `.\scripts\iniciar_dev.ps1` |
| Modo | `prod`: estável, não recarrega ao editar código | `dev`: recarrega a cada arquivo salvo |

O IP da produção fica em `C:\HARLEY_PROD\producao.local.ps1`, fora do git.
O Wi-Fi deste notebook (adaptador `4C-5F-70-A2-40-1D`, rede `SIDLAR_2G`)
está com **IP fixo 192.168.0.12**, configurado no Windows por
`scripts\ip_do_servidor.ps1` (como administrador). Com IP fixo o notebook
não conecta direito em outras redes: para usá-lo fora da loja, rode
`.\scripts\ip_do_servidor.ps1 -Automatico`, e `-Fixo` ao voltar. Se o IP
mudar, edite `producao.local.ps1` e rode `.\scripts\atualizar_producao.ps1`.
(O ideal, quando houver a senha do modem Claro, é trocar o IP fixo por uma
reserva de DHCP no modem.)

### Levar uma alteração para a produção

1. Teste no desenvolvimento e faça o commit (`git add -A` e `git commit -m "..."`).
2. Rode `.\scripts\publicar.ps1`. Ele recusa se houver algo sem commit,
   cria a tag `prod-AAAAMMDD-HHMM`, envia ao GitHub e reinicia a produção
   nessa versão. Os funcionários ficam cerca de 1 minuto sem o sistema,
   enquanto ele recompila.

### Voltar para a versão anterior

```powershell
git tag --list "prod-*"                                # versões publicadas
.\scripts\atualizar_producao.ps1 -Tag prod-AAAAMMDD-HHMM
```

### Parar a produção

`.\scripts\parar_producao.ps1`. **Não** use "Encerrar" no Agendador de
Tarefas: isso deixa processos órfãos segurando as portas 3000/8000, que só
somem reiniciando o notebook.

Os registros ficam em `C:\HARLEY_PROD\logs\` (`producao-*.log` = saída do
sistema; `supervisor-*.log` = início e parada).

### Configuração do Windows (já aplicada)

`scripts\configurar_windows.ps1` (como administrador) deixa o notebook
pronto para servir durante o expediente: rede como Privada, nunca
suspender na tomada, tampa fechada não suspende, horário ativo do Windows
Update das 7h às 19h (reinícios automáticos só à noite), firewall e a
tarefa de início automático. Pode ser executado de novo sem duplicar nada.

### ⚠️ Os dois ambientes usam o MESMO banco Xano

Não existe um banco "de teste": o que se faz no desenvolvimento altera os
dados reais da loja. Teste só com registros claramente marcados como teste
(por exemplo, com "TESTE" no nome) e apague-os em seguida. Não faça testes
de estoque em produtos reais.

Na primeira vez que abrir, todas as listas estarão vazias. Cadastre nesta
ordem, porque uma tela depende da outra (é a mesma ordem de dependência das
chaves estrangeiras do banco original):

`Funcionários` e `Fornecedores` → `Produtos` → `Clientes` → `Motos dos clientes`
→ aí sim `Vendas`, `Ordens de serviço` e `Compras`.

## Estrutura do projeto

```
C:\LOJA-EXTRA-HARLEY\
├── AGENTS.md                ← regras de trabalho para agentes de IA (CLAUDE.md aponta para ele)
├── docs/
│   ├── project-overview.md  ← visão geral: problema, usuários, escopo, arquitetura
│   └── domain-model.md      ← conceitos do negócio e seus relacionamentos
├── rxconfig.py              ← configuração do Reflex (sem banco local: db_url=None)
├── requirements.txt         ← dependências Python (gerado por pip freeze)
├── skills-lock.json         ← versão instalada das Agent Skills do Reflex
├── .env                     ← credenciais (conta de serviço do Xano, SendGrid, Asaas); fora do git
├── harley_store/
│   ├── harley_store.py      ← ponto de entrada: rotas, proteção das ações e tarefa do cache
│   ├── xano_client.py       ← acesso aos dados no Xano (cópia em memória, novas tentativas)
│   ├── xano_auth_client.py  ← login e conferência da sessão
│   ├── xano_admin_client.py ← administração das contas (tela Usuários)
│   ├── sessao.py            ← barra no servidor as ações de quem não tem sessão
│   ├── estoque.py           ← toda movimentação de estoque (travas e histórico)
│   ├── vendas_servico.py    ← registro e cancelamento de vendas
│   ├── pagamentos_servico.py ← forma de pagamento, cobrança e confirmação (Asaas)
│   ├── asaas_client.py      ← acesso à API do Asaas (cobranças)
│   ├── dependencias.py      ← impede excluir cadastro que está em uso
│   ├── validacao.py         ← CPF/CNPJ, e-mail, telefone, números e imagens
│   ├── constantes.py        ← listas fixas das telas (tipos de venda, situações da OS...)
│   ├── fotos_oficiais.py    ← fotos oficiais dos modelos (arquivos em assets/motos/)
│   ├── email_clientes.py    ← e-mails aos clientes (SendGrid), inclusive a confirmação de pagamento
│   ├── erros.py             ← mensagens de erro em português e logs
│   ├── components/          ← menu (layout.py), cores (tema.py) e peças comuns das telas
│   ├── state/               ← um arquivo por tela: dados + regras (ex.: produtos_state.py)
│   └── pages/               ← um arquivo por tela: só a parte visual (ex.: produtos.py)
├── assets/                  ← logo, ícones do app, spinner e fotos oficiais (motos/)
├── scripts/                 ← operação: iniciar, publicar, aplicar o Xano, reparos e testes
├── tests/                   ← testes automáticos (sem tocar no Xano real)
├── xano/                    ← espelho do Xano: tabelas (table/) e endpoints (api/)
├── xano_import/             ← CSVs da importação inicial dos dados para o Xano
├── openspec/                ← especificações (specs/) e mudanças (changes/), ver OpenSpec
├── .agents/skills/          ← Agent Skills do Reflex (npx skills add reflex-dev/agent-skills)
├── .github/                 ← workflows do OpenSpec para o GitHub Copilot (prompts/ e skills/)
└── .claude/                 ← workflows do OpenSpec para o Claude Code e cópia das skills do Reflex
```

Cada tela é **sempre** o par `state/algo_state.py` + `pages/algo.py`. O
`state` guarda os dados carregados do Xano e os métodos que salvam,
editam e excluem; a `page` só desenha a tela e chama os métodos do state
quando o usuário clica em algo. Separar assim é o que deixa fácil mexer
numa tela sem quebrar as outras. Exceção: a aba Motos de Produtos usa
`pages/motos_loja.py` como uma seção dentro de `pages/produtos.py`, com o
state `state/motos_loja_state.py`.

### Como alterar a estrutura do banco (Xano)

O banco é o Xano; não há banco local nem migrações no app.

1. Registre a mudança no OpenSpec (`/opsx:propose "..."`), dizendo qual
   tabela ou campo muda e por quê. Lembre que a equipe evita campos e
   tabelas desnecessários no Xano.
2. Altere o espelho na pasta `xano/`: os campos ficam em
   `xano/table/<tabela>.xs`; se o endpoint de criação (`POST`) ou de
   substituição (`PUT`) lista os campos um a um, acrescente o campo novo
   nele também (`xano/api/harley/...`).
3. Confira a prévia, que não grava nada:

   ```powershell
   .\scripts\aplicar_xano.ps1 -SoPrevia
   ```

   Uma tabela no espelho **substitui** a definição inteira no Xano: se
   aparecer na prévia uma tabela que você não alterou, confira antes se o
   espelho não está sem algum campo que existe no Xano, para não apagar
   dados.
4. Aplique (a CLI pede confirmação e nunca apaga tabelas nem endpoints):

   ```powershell
   .\scripts\aplicar_xano.ps1
   ```

5. Ajuste o código. Tabela nova usada pelas telas entra em
   `TABELAS_AQUECIDAS` (`harley_store/xano_client.py`); se ela aponta para
   outra, entra em `REFERENCIAS` (`harley_store/dependencias.py`).
6. Tela nova: copie um par `state/*.py` + `pages/*.py` parecido (o de
   `Fornecedores` é o mais simples; o de `Compras` mostra o padrão
   "cabeçalho + itens", usado também em Ordens de Serviço), registre a rota
   em `harley_store/harley_store.py` (com `AuthState.exigir_login` como
   primeiro item do `on_load` e o state na lista do `ExigeSessaoMiddleware`)
   e o link no menu em `harley_store/components/layout.py` (`MENU_ITEMS`).

### Vendas antigas (antes do registro de itens)

Vendas registradas antes de existirem os itens (tabela `itens_transacao`)
guardam só o valor total. Elas continuam aparecendo e podem ser canceladas,
mas nesse caso nada volta ao estoque automaticamente, porque não se sabe o
que foi vendido; o sistema avisa para conferir o estoque manualmente.

## Regras de integridade (estoque, cadastros e sessão)

- **Estoque:** toda alteração de saldo (venda, cancelamento, peças de OS,
  compras, exclusão de OS/compra e edição do cadastro de produto) passa por
  `harley_store/estoque.py`, com trava por produto e releitura do Xano. O
  saldo nunca fica negativo, nenhuma movimentação simultânea se perde e,
  se uma gravação falhar no meio, o que já foi feito é desfeito. Na edição
  de um produto, vale a **variação** digitada: se houve uma venda enquanto
  o formulário estava aberto, ela é preservada.
- **Exclusões:** um cadastro usado em outro lugar não pode ser excluído
  (cliente com motos ou vendas, produto usado em vendas/OS/compras,
  funcionário com vendas/OS, fornecedor com compras, moto com OS). As
  ligações ficam em `harley_store/dependencias.py`.
- **Validações no servidor** (`harley_store/validacao.py`): CPF/CNPJ com
  dígitos verificadores (gravados sempre formatados, e a duplicidade é
  conferida pelos números), e-mail, telefone com DDD, placa (antiga ou
  Mercosul), chassi, valores e quantidades. Fotos são conferidas pelo
  conteúdo, não só pela extensão (máximo 5 MB).
- **Sessão:** o login é conferido no Xano (`auth/me`), não basta existir
  o cookie; ele vence em 24 h, junto com o token. Toda ação das telas é
  barrada no servidor para quem não tem sessão válida
  (`harley_store/sessao.py`), inclusive eventos mandados direto pelo
  websocket. Um state novo precisa entrar na lista do
  `ExigeSessaoMiddleware` em `harley_store/harley_store.py`.
- **Erros:** falhas inesperadas aparecem ao funcionário como uma mensagem
  clara em português; os detalhes vão para o log (na produção,
  `logs\producao-*.log`), sem senhas nem tokens.

## Testes automáticos

Rodam sem internet e sem tocar no Xano (o estoque é testado com um Xano
simulado, incluindo vendas simultâneas):

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Contas, perfis e senhas

- Não existe cadastro público: só um **administrador** cria contas, na tela
  **Usuários do sistema** (que só aparece para administradores). Lá ele
  também troca o e-mail, define uma nova senha, muda o perfil
  (Administrador / Funcionário) e exclui contas.
- **Esqueci minha senha:** a pessoa pede a um administrador, que define
  uma nova senha para ela. (Antes, qualquer um trocava a senha de qualquer
  conta sabendo só o e-mail.)
- O Xano confere o perfil em toda operação de administração; um
  funcionário comum recebe "sem permissão" mesmo chamando a API direto.
- Ninguém altera o próprio perfil nem exclui a própria conta, então sempre
  sobra ao menos um administrador.
- Toda conta nova recebe um e-mail de boas-vindas no e-mail cadastrado
  (ver [E-mails automáticos (SendGrid)](#e-mails-automáticos-sendgrid)).
  Funcionários (tela Funcionários) são o cadastro de RH, sem login e sem
  e-mail: quem usa o sistema precisa de uma conta de usuário.

## Segurança da API do Xano e conta de serviço

Todos os endpoints de dados do Xano exigem login. O **servidor** do app
acessa os dados com uma **conta de serviço** própria ("Sistema Harley
Store"), cujas credenciais ficam no arquivo `.env` da pasta de cada
ambiente (desenvolvimento e `C:\HARLEY_PROD`), **fora do git**:

```
HARLEY_XANO_EMAIL=...
HARLEY_XANO_SENHA=...
```

Sem esse arquivo o app não consegue ler nem gravar nada (o log mostra
`HARLEY_XANO_EMAIL/HARLEY_XANO_SENHA ausentes`). Numa instalação nova,
copie o `.env` de uma pasta existente. **Não exclua** a conta "Sistema
Harley Store" na tela de usuários.

Se todas as telas mostrarem "Você não tem permissão para esta operação" e
listas vazias, o Xano está recusando a conta de serviço (senha trocada ou
conta excluída). Para reparar, rode e entre com uma conta de administrador:

```powershell
.venv\Scripts\python.exe scripts\reparar_conta_servico.py
```

Ele gera uma senha nova para a conta de serviço (ou a recria), grava no
Xano e no `.env` (e, se você confirmar, no `C:\HARLEY_PROD\.env`) e testa a
leitura dos dados. Depois, reinicie o app.

As definições do Xano (tabelas e endpoints) ficam espelhadas na pasta
`xano\`. Para aplicar mudanças feitas nela:

```powershell
.\scripts\aplicar_xano.ps1 -SoPrevia   # mostra o que mudaria
.\scripts\aplicar_xano.ps1             # mostra e pede confirmação
```

`-Reverter` volta os endpoints ao estado de antes da auditoria de
24/09/2026 (API aberta), só para emergência.

## Spinner de carregamento nos botões

Qualquer botão que dispare uma ação no servidor mostra um círculo girando
até a ação terminar. Se o botão some da tela (diálogo que fecha, troca de
página), aparece um spinner laranja no centro. Funciona em todas as telas,
inclusive nas futuras, sem mexer em nenhuma delas: `assets/carregando.js`
observa as mensagens do websocket do Reflex, e o visual fica em
`assets/carregando.css`.

## Fotos

- Todas as fotos (motos da loja, produtos e motos de clientes) vão para o
  armazenamento do Xano pelo endpoint `POST motos/foto` (campo `arquivo`),
  então aparecem igual na produção e no desenvolvimento. Fotos antigas de
  produtos/motos de clientes, guardadas em `uploaded_files/`, continuam
  aparecendo.
- Motos da loja: uma foto principal e até 8 adicionais; qualquer adicional
  pode virar a principal. O botão de ampliar no cartão abre a galeria.
- **Fotos oficiais**: em `assets/motos/` ficam as fotos de fábrica (site
  harley-davidson.com) de 10 modelos: Iron 883, Fat Boy 114, Heritage
  Classic, Sportster S, Pan America 1250 Special, Street Glide Special,
  Road Glide Limited, Low Rider S, Breakout 117 e Nightster Special. Moto da
  loja ou de cliente sem foto enviada mostra a oficial, escolhida pelo
  **nome do modelo cadastrado** (modelo não reconhecido fica sem foto, nada
  é inventado). Para incluir outro modelo: salve a foto em `assets/motos/`
  e acrescente uma linha em `harley_store/fotos_oficiais.py`. Elas não
  ocupam o armazenamento do Xano.
- Para cadastrar no estoque da loja os modelos acima que ainda não estão lá,
  rode uma vez `.venv\Scripts\python.exe scripts\cadastrar_motos_catalogo.py`
  (mostra a prévia e pede confirmação). Eles entram como unidades 0 km,
  **sem placa e sem chassi**: as placas e chassis da lista original são das
  motos dos clientes, e repeti-los faria a mesma moto existir duas vezes.
  Chassi, ano, cor e preços são preenchidos quando a unidade chegar.
- Aceitos: PNG, JPG e WEBP (produtos e motos de clientes também GIF), até
  5 MB; o conteúdo do arquivo é conferido, não só a extensão.
- Ao excluir uma moto, a foto continua guardada no Xano (o plano não
  oferece exclusão de arquivo pela API); isso não aparece para ninguém.

## E-mails automáticos (SendGrid)

O app envia, pelo [SendGrid](https://sendgrid.com), um e-mail de
**boas-vindas** quando um cliente com e-mail é cadastrado e um de
**parabéns pela compra** quando uma moto da loja é marcada como Vendida para
um cliente com e-mail. Quando um administrador cria uma **conta de acesso**
(tela Usuários do sistema), a pessoa recebe no e-mail da conta um
**e-mail de boas-vindas à equipe**, que explica que o login é o próprio
e-mail e que a senha é entregue pessoalmente (a senha nunca vai no e-mail).
O envio sai direto do servidor do app (não usa o
Xano), em segundo plano: uma falha só aparece no log e nunca desfaz o
cadastro ou a venda. Para ligar, acrescente ao `.env` de cada pasta (produção
e desenvolvimento):

    SENDGRID_API_KEY=SG.xxxxxxxx
    SENDGRID_REMETENTE=contato@sualoja.com.br
    SENDGRID_REMETENTE_NOME=Harley Store

A chave é criada no SendGrid em *Settings > API Keys* (permissão "Mail
Send"), e o remetente precisa estar verificado em *Settings > Sender
Authentication*. Sem essas linhas, nenhum e-mail é enviado e o app funciona
normalmente. Os textos ficam em `harley_store/email_clientes.py`.

Para conferir a configuração (chave, permissão de envio, remetente
verificado) e mandar um e-mail de teste:

```powershell
.venv\Scripts\python.exe scripts\testar_sendgrid.py
```

## Pagamentos pelo Asaas

Ao concluir uma venda em **Vendas / Balcão**, o funcionário escolhe a
**forma de pagamento**:

| Forma | O que acontece |
|---|---|
| **Na loja** (padrão) | Dinheiro ou maquininha. Nada é enviado ao Asaas. |
| **Boleto** | Cobrança por boleto no Asaas. |
| **Cartão de crédito** | Cobrança por cartão: o cliente digita os dados do cartão na página do Asaas (eles nunca passam pelo sistema). |
| **Cliente escolhe** | O link do Asaas oferece boleto, cartão ou Pix. |

Nas formas pelo Asaas o funcionário informa o **vencimento** (padrão: 3
dias), e a venda exige um **cliente com CPF/CNPJ válido e e-mail ou
celular**. O servidor procura o cliente no Asaas pelo CPF/CNPJ (ou o cria,
com as notificações ligadas) e gera a cobrança, que o **próprio Asaas envia
ao cliente por e-mail e SMS**. A lista de vendas mostra a situação do
pagamento (Aguardando pagamento, Pago, Vencido, Cobrança cancelada ou
Falha na cobrança) e o link **Abrir cobrança**.

- **Falha na cobrança:** se o Asaas não responder, a venda continua
  registrada e aparece o botão **Gerar cobrança de novo** (ele reaproveita
  a cobrança se ela chegou a ser criada; nunca cobra duas vezes).
- **Confirmação:** o servidor fica na rede da loja e não recebe avisos da
  internet (webhook). Por isso ele **consulta o Asaas a cada 5 minutos**
  (ajustável) e também quando alguém clica em **Atualizar pagamentos**.
  Quando a cobrança é paga, a venda passa a **Pago** e o cliente recebe pelo
  SendGrid o e-mail **"Pagamento confirmado"** (uma única vez).
- **Cancelamento:** cancelar a venda cancela a cobrança em aberto no Asaas.
  Se a venda já estava paga, o estorno é feito no painel do Asaas.
- **Painel:** a venda continua contando no faturamento no dia do registro.

### Configuração

Acrescente ao `.env` de cada pasta (produção e desenvolvimento):

    ASAAS_API_KEY=$aact_...
    ASAAS_AMBIENTE=sandbox
    ASAAS_INTERVALO_MINUTOS=5

A chave é criada no painel do Asaas em *Integrações > Chaves de API*. Por
enquanto só o ambiente **Sandbox** (testes, sem dinheiro real,
https://sandbox.asaas.com) é aceito. Sem a chave, só a forma "Na loja"
aparece e o app funciona como antes. A integração também precisa dos campos
de pagamento em `transacoes` no Xano (`forma_pagamento`,
`situacao_pagamento`, `asaas_cobranca_id`, `link_cobranca` e
`data_pagamento`), aplicados com `scripts\aplicar_xano.ps1`. Sem eles, as
formas pelo Asaas são recusadas com um aviso. O código fica em
`harley_store/asaas_client.py` e `harley_store/pagamentos_servico.py`.

Para conferir a chave e, opcionalmente, criar e remover um boleto TESTE no
Sandbox:

```powershell
.venv\Scripts\python.exe scripts\testar_asaas.py
.venv\Scripts\python.exe scripts\testar_asaas.py --cobranca-teste
```

**Testar no Sandbox:** registre uma venda com boleto para um cliente TESTE
(com o seu e-mail e celular); no painel do Sandbox, abra a cobrança e use
**Confirmar recebimento** (ou pague com um cartão de teste do Asaas); depois
clique em **Atualizar pagamentos** e confira o e-mail de confirmação. No
Sandbox o Asaas pode não enviar SMS de verdade.

## Histórico de estoque

Cada entrada e saída (venda, cancelamento, peça em OS, compra, exclusões,
cadastro e ajuste manual) é registrada na tabela `movimentacoes_estoque`
com data, quantidade, saldo depois da operação, documento de origem e
usuário. Em **Produtos**, o botão **Histórico** mostra as movimentações de
cada produto.

## OpenSpec

O projeto usa o [OpenSpec](https://github.com/Fission-AI/OpenSpec) para
registrar o que o sistema faz e cada mudança feita nele. O contexto que a IA
recebe vem de quatro documentos:

| Documento | Pergunta que responde |
|---|---|
| `docs/project-overview.md` | O que é o projeto? |
| `docs/domain-model.md` | Quais são os conceitos e relacionamentos? |
| `AGENTS.md` | Como o agente deve trabalhar neste projeto? |
| `openspec/config.yaml` | Que contexto, regras (`rules`) e orientações (`operations`) os workflows recebem? |

Os workflows do OpenSpec (OpenSpec 1.14.1) ficam em `.claude/` (Claude Code)
e em `.github/` (GitHub Copilot), instalados pelo `openspec init`. Para
reinstalá-los depois de atualizar o OpenSpec: `openspec update`.

- **`openspec/specs/`** — o comportamento atual do sistema, organizado por
  domínio: `plataforma/`, `vendas/`, `estoque/`, `cadastros/`, `clientes/`,
  `compras/`, `documentos/`, `motos/`, `oficina/`, `painel/` e `produtos/`.
- **`openspec/changes/`** — mudanças em andamento. Em 11/11/2026:
  `pagamento-de-vendas-pelo-asaas` (forma de pagamento na venda, cobrança
  pelo Asaas Sandbox e e-mail de confirmação de pagamento). O código está
  implementado e os campos já estão no Xano; falta só a conferência da tela
  no navegador e do e-mail real de confirmação (tarefa 6.4).
- **`openspec/changes/archive/`** — mudanças concluídas, com proposta,
  desenho e tarefas. A data no nome de cada pasta é o dia em que o recurso
  ficou pronto (conforme os commits). A `acesso-em-rede-local` foi arquivada
  incompleta, por decisão do grupo: as verificações que exigem a produção
  ligada na rede da loja estão listadas no `tasks.md` dela.

Toda mudança no sistema passa pelo fluxo:

1. `/opsx:explore` — investiga a ideia e o código, sem criar arquivos;
2. `/opsx:propose "sua ideia"` — cria a proposta, as especificações, o
   desenho e as tarefas;
3. **revisão** — o grupo lê e aprova ou corrige os artefatos;
4. `/opsx:apply` — implementa as tarefas, marcando cada uma;
5. `/opsx:verify` — confere se o que foi feito corresponde às especificações,
   às tarefas e ao desenho;
6. `/opsx:archive` — atualiza `openspec/specs/` e arquiva a mudança.

No GitHub Copilot os mesmos comandos usam hífen: `/opsx-propose`,
`/opsx-apply`, `/opsx-verify` etc.

Para consultar: `openspec list` (mudanças abertas), `openspec list --specs`
(especificações) e `openspec validate --all --strict` (validação).

## Backup

Os dados da loja (clientes, produtos, vendas, OS, motos, usuários) ficam
no **Xano**, não neste computador. Para ter uma cópia, exporte as tabelas
pelo painel do Xano (Database → cada tabela → Export CSV) periodicamente e
guarde os arquivos fora do notebook (pen drive ou nuvem).

O banco SQLite do início do projeto (`harley_store.db`, `models.py` e
`alembic/`) foi removido em 07/10/2026 e continua no histórico do git. As
fotos antigas de **produtos** e de **motos de clientes** ficam em
`uploaded_files/` na pasta de cada ambiente (na produção,
`C:\HARLEY_PROD\uploaded_files`); copie essa pasta junto com o backup.
