# Design

## Context

Estado atual, verificado no notebook servidor (motivação em proposal.md, requisitos em `specs/plataforma/acesso-em-rede-local/spec.md`):

- `rxconfig.py` não define `api_url`; o Reflex 0.7.14 usa `http://localhost:8000`. O backend já escuta em `0.0.0.0`.
- O Reflex lê qualquer campo da configuração a partir de variáveis de ambiente com o prefixo `REFLEX_` (por exemplo `REFLEX_API_URL`, `REFLEX_FRONTEND_PORT`, `REFLEX_BACKEND_PORT`). O `api_url` é gravado no frontend durante a compilação.
- Em `--env prod`, o frontend é compilado (`next build`) e servido por `next start`, sem recarregar quando arquivos mudam. Em `--env dev`, qualquer alteração de arquivo recompila e reinicia.
- Notebook no Wi-Fi "Sidlar" (perfil **Público**), IP `192.168.0.54` por DHCP, adaptador `ec:0e:c4:f6:76:0d` (endereço de hardware, não aleatório). Suspende após 15 min na tomada. Horário ativo do Windows Update: 15h–23h.
- Não existem regras de firewall de entrada para `python`, `node` ou `bun`: o Windows bloqueia por padrão qualquer porta não liberada.
- A pasta do projeto não é um repositório git, e o Git não está instalado. O `.gitignore` já exclui `.web/`, `.venv/`, `*.db`, `uploaded_files/`, `*.log` e `.env`.
- Os dois ambientes usarão o mesmo backend Xano (decisão registrada no proposal).

## Goals / Non-Goals

**Goals:**
- Nenhum endereço de rede no código versionado: tudo o que muda por ambiente vem de variáveis de ambiente definidas pelos scripts de execução.
- Operação do dia a dia por scripts PowerShell versionados, sem o usuário precisar lembrar de comandos do Reflex.
- Cada item de configuração do Windows e do roteador tem um passo de verificação objetivo.

**Non-Goals:**
- Transformar o backend em serviço do Windows (NSSM, serviço nativo). O Agendador de Tarefas atende o requisito com menos peças.
- Monitoramento, alertas ou reinício automático se o processo cair durante o dia (ver Riscos).
- Mudar telas, states ou o cliente Xano.

## Decisions

### D1. Configuração por variáveis de ambiente, não por código
Os scripts definem `REFLEX_API_URL`, `REFLEX_FRONTEND_PORT` e `REFLEX_BACKEND_PORT` antes de chamar `reflex run`. O `rxconfig.py` continua com os padrões de desenvolvimento local e ganha apenas um comentário apontando para os scripts.
- *Alternativa:* `api_url` fixo no `rxconfig.py` com o IP da loja. Rejeitada: o arquivo é versionado e compartilhado pelos dois ambientes, e trocar o IP exigiria um commit.
- *Alternativa:* `REFLEX_ENV_FILE`. Rejeitada por depender de pacote extra de leitura de `.env`; o script PowerShell resolve sem dependência nova.

O endereço de produção fica em um arquivo local **não versionado** na pasta de produção (`producao.local.ps1`, que define o IP reservado), lido pelo script de início. O `.gitignore` passa a excluí-lo.

### D2. Portas e ambientes

| Ambiente | Pasta | Modo | Frontend | Backend | `REFLEX_API_URL` |
|---|---|---|---|---|---|
| Produção | `C:\HARLEY_PROD` (clone) | `prod` | 3000 | 8000 | `http://<IP reservado>:8000` |
| Desenvolvimento | `C:\TESTE_LOJA_HARLEY` | `dev` | 3001 | 8001 | `http://localhost:8001` |

Mantém os endereços que já estão no README e na memória dos usuários (3000) para a produção; o desenvolvimento muda de porta.
- *Alternativa:* produção em outras portas e desenvolvimento em 3000/8000. Rejeitada: a produção é o que mais gente acessa, e o endereço dela deve ser o "normal".

### D3. Isolamento da rede para o desenvolvimento via firewall
Regra de entrada liberando **somente TCP 3000 e 8000, perfil Privado**. Como não há regras genéricas para `python`/`node`, as portas 3001/8001 ficam bloqueadas para outros aparelhos sem configuração adicional. O script de desenvolvimento também define `REFLEX_BACKEND_HOST=127.0.0.1`, como segunda barreira para o backend de desenvolvimento.
- *Alternativa:* regra por programa (`python.exe`). Rejeitada: liberaria também o desenvolvimento, que usa o mesmo executável.

### D4. Git local, produção como clone, versões marcadas com tag
`git init` em `C:\TESTE_LOJA_HARLEY`; `C:\HARLEY_PROD` é um `git clone` dessa pasta. Cada publicação cria uma tag `prod-AAAAMMDD-HHMM` no repositório de desenvolvimento, e a produção faz checkout da tag. Voltar à versão anterior é fazer checkout da tag anterior e reiniciar.
- *Alternativa:* cópia com `robocopy`. Rejeitada na exploração: não registra versão nem permite rollback.
- **Remoto no GitHub (adotado depois, a pedido do usuário):** o repositório privado `marcelomuranaka-spec/LOJA-EXTRA-HARLEY` é o `origin` do desenvolvimento e serve como cópia do código fora do notebook. O roteiro de publicação continua local: a produção clona e atualiza a partir de `C:\TESTE_LOJA_HARLEY`, sem depender da internet para publicar. O repositório MUST continuar privado enquanto a API do Xano não exigir token, porque as URLs dela estão no código.

A produção tem seu próprio `.venv` (criado a partir de `requirements.txt`) e sua própria `uploaded_files/`. O `.gitignore` passa a excluir também `.states/`, e `harley_store.db` já está excluído por `*.db`.

### D5. Scripts de operação (versionados em `scripts/`)
- `iniciar_producao.ps1`: carrega `producao.local.ps1`, define as variáveis e roda `reflex run --env prod` na pasta de produção, com a saída gravada em `logs/producao-AAAAMMDD.log`.
- `parar_producao.ps1`: pede a parada criando `logs\PARAR` na pasta de produção, espera as portas liberarem e, por fim, encerra o que ainda for visível nesta sessão (a árvore de processos de `C:\HARLEY_PROD`).
  - **Ajuste feito no Apply:** a tarefa agendada com logon S4U roda na sessão 0 do Windows, e os processos criados lá não podem ser vistos nem encerrados pelo usuário comum ("Acesso negado", linha de comando vazia). Por isso `iniciar_producao.ps1` virou um **supervisor**: inicia o Reflex, vigia o arquivo `logs\PARAR` e, ao encontrá-lo, encerra a própria árvore de processos, com a qual compartilha a sessão. Encerrar a tarefa pelo Agendador NÃO é usado para parar, porque mata o supervisor antes dos filhos e deixa um órfão segurando a porta (foi o que aconteceu na primeira tentativa).
  - *Alternativas rejeitadas:* rodar `publicar` sempre como administrador (UAC a cada publicação); tarefa só com o usuário conectado (viola o retorno automático após reinício).
- `atualizar_producao.ps1 [-Tag <tag>]`: parar → `git fetch` → `git checkout <tag>` (ou a tag mais recente) → `pip install -r requirements.txt` → iniciar via Agendador. Recusa-se a rodar se a pasta de produção tiver alterações locais.
- `publicar.ps1`: no desenvolvimento, recusa-se a rodar se houver alterações não commitadas, cria a tag `prod-...` e chama `atualizar_producao.ps1`.
- `iniciar_dev.ps1`: portas 3001/8001, backend em `127.0.0.1`, `--env dev`.

### D6. Início automático pelo Agendador de Tarefas, gatilho "ao iniciar o sistema"
Tarefa `HarleyStore-Producao` com gatilho **na inicialização**, executando `iniciar_producao.ps1` com a conta do usuário, na opção "executar estando o usuário conectado ou não", sem armazenar senha (logon S4U). Com "reiniciar se falhar" (3 tentativas, intervalo de 1 min) e sem limite de tempo de execução.
- *Alternativa:* gatilho "ao fazer logon". Rejeitada: após um reinício noturno do Windows Update, o sistema ficaria fora do ar até alguém entrar no notebook, o que viola o requisito de retorno automático.
- *Alternativa:* armazenar a senha na tarefa. Só será usada se o S4U não conseguir acessar a internet ou os arquivos do usuário na verificação da tarefa 4.x; o S4U só perde acesso a recursos de rede autenticados (compartilhamentos), que o sistema não usa.

### D7. Configuração do Windows e do roteador

| Item | Configuração | Verificação |
|---|---|---|
| Rede "Sidlar" | Perfil Privado | `Get-NetConnectionProfile` mostra `Private` |
| Suspensão na tomada | Nunca (`powercfg /change standby-timeout-ac 0`) | `powercfg /query` mostra índice AC `0x0` |
| Tampa fechada na tomada | Não fazer nada (LIDACTION AC = 0) | `powercfg /query ... LIDACTION` e teste físico |
| Suspensão na bateria | Mantida (10 min) | Sem mudança |
| Horário ativo do Windows Update | 7h–19h | Configurações > Windows Update > Horário ativo |
| Reserva de IP | No roteador, para `ec:0e:c4:f6:76:0d` | IP igual após reconectar o Wi-Fi |
| Endereço aleatório de hardware | Desligado para a rede "Sidlar" | `netsh wlan show interfaces` mantém `ec:0e:c4:f6:76:0d` |

A regra de horário ativo é a mesma para todos os dias no Windows; 7h–19h cobre os dias úteis (8h–18h) e o fim de semana (9h–16h).

## Risks / Trade-offs

- **[Processo cai durante o expediente e não volta]** → A tarefa reinicia após falha de início, mas não monitora o processo durante o dia. Mitigação: `iniciar_producao.ps1` fica em execução enquanto o Reflex roda, então o "reiniciar se falhar" do Agendador cobre a saída inesperada. Monitoramento completo fica fora do escopo.
- **[Início lento]** → `reflex run --env prod` recompila o frontend a cada início (alguns minutos). É aceitável porque os reinícios acontecem fora do expediente. O tempo real será medido na verificação.
- **[IP reservado muda (troca de roteador)]** → Basta editar `producao.local.ps1` e reiniciar a tarefa; a recompilação acontece no início.
- **[Mesmo Xano nos dois ambientes]** → Risco aceito no proposal; disciplina de testes até a change de separação de dados.
- **[Fotos em `uploaded_files/` diferentes por ambiente]** → Aceito; registrado para decisão futura sobre o storage de imagens.
- **[Wi-Fi]** → Sinal de 100% no local atual; se o notebook mudar de lugar, a qualidade do acesso depende do Wi-Fi. Cabo continua sendo a opção mais estável, fora do escopo.
- **[Comandos que exigem administrador]** → Firewall, perfil da rede, `powercfg` para a tampa e a tarefa agendada exigem elevação. Serão executados pelo usuário ou com autorização explícita no Apply, nunca de forma implícita.

## Migration Plan

1. Pré-requisitos manuais (Git, perfil de rede, energia, Windows Update, reserva de IP), cada um verificado.
2. Versionamento: `git init`, ajuste do `.gitignore`, commit inicial.
3. Scripts e ajuste do `rxconfig.py` (apenas comentário); commit.
4. Criação da produção: clone em `C:\HARLEY_PROD`, `.venv`, `producao.local.ps1`, primeira publicação.
5. Firewall e tarefa agendada.
6. Verificação completa (acesso de outro aparelho, reinício, isolamento do desenvolvimento, rollback).
7. README atualizado.

**Rollback da change inteira:** desabilitar a tarefa `HarleyStore-Producao`, remover a regra de firewall e voltar a rodar `reflex run` na pasta de desenvolvimento, como hoje. As configurações de energia e do Windows Update podem permanecer, porque são inofensivas.

## Open Questions

- Tempo real de subida da produção após o reinício: medido na verificação, e só registrado no README.
- Se o S4U impedir a tarefa de funcionar, troca-se para "armazenar senha" (D6), sem mudar os requisitos nem as tarefas.
