# Proposal

## Why

Hoje o Harley Store só funciona no próprio notebook onde roda: o frontend aponta o backend para `http://localhost:8000` (valor padrão do Reflex, sem `api_url` configurado), então em qualquer outro aparelho da rede a tela abre, mas nunca conecta. A loja precisa que outros funcionários usem o sistema a partir de outros computadores e celulares da rede interna, durante todo o expediente (segunda a sexta das 8h às 18h; sábado e domingo das 9h às 16h).

Além do endereço, o ambiente atual derrubaria o sistema para todos: o notebook suspende após 15 minutos na tomada, a rede "Sidlar" está marcada como Pública (bloqueia conexões de entrada), o Windows Update pode reiniciar entre 23h e 15h (cobrindo a manhã de expediente) e nada sobe sozinho após um reinício. Como o mesmo notebook também é usado para desenvolver o sistema, a instância usada pelos funcionários precisa ficar isolada do desenvolvimento, para que editar código não derrube uma venda em andamento.

## What Changes

- O sistema passa a ser acessível por outros aparelhos da rede interna em um endereço fixo do notebook servidor (reserva de IP no roteador).
- O endereço do backend (`api_url`) passa a ser configurável por ambiente: produção usa o endereço fixo da rede; desenvolvimento continua em `localhost`.
- Passam a existir dois ambientes no mesmo notebook, em pastas separadas:
  - produção, usada pelos funcionários: modo `prod`, portas 3000/8000, liberadas no firewall apenas para a rede Privada;
  - desenvolvimento, a pasta atual: modo `dev`, outras portas, acessível só localmente.
- O projeto passa a ser versionado com **git** (hoje a pasta não é um repositório). A pasta de produção é um clone local, e atualizar a produção segue um roteiro definido: dev → commit → atualizar o clone de produção → recompilar → reiniciar.
- A produção sobe automaticamente quando o notebook liga ou reinicia.
- Pré-requisitos de ambiente, feitos manualmente pelo administrador do Windows e do roteador, com verificação:
  - instalar o Git for Windows;
  - rede "Sidlar" como Privada;
  - reserva de IP no roteador para o adaptador Wi-Fi do notebook;
  - não suspender na tomada, e fechar a tampa não fazer nada;
  - horário ativo do Windows Update das 7h às 19h, cobrindo o expediente com 1h de folga.
- O README deixa de orientar "deixe o terminal aberto" e passa a documentar os dois ambientes e o roteiro de atualização.

Fora do escopo desta change: separar os dados de desenvolvimento e produção (os dois ambientes continuam usando o mesmo Xano; até uma change própria, testes no desenvolvimento só com registros marcados como teste e sem testes de estoque em produtos reais), HTTPS, perfis de acesso, validação de sessão e proteção da API do Xano.

## Capabilities

### New Capabilities
- `plataforma/acesso-em-rede-local`: disponibilidade do sistema para os aparelhos da rede interna da loja. Cobre o endereço fixo de acesso, a separação entre os ambientes de produção e desenvolvimento, o início automático, a permanência no ar durante o expediente e o roteiro de atualização da produção.

### Modified Capabilities
<!-- Nenhuma: o projeto ainda não tem specs. -->

## Impact

- **Código**: `rxconfig.py` (`api_url` e portas por ambiente, via variáveis de ambiente); nenhuma tela ou state muda.
- **Repositório**: `git init` nesta pasta; revisão do `.gitignore`; nova pasta de produção fora deste diretório (clone).
- **Operação/Windows**: regras de firewall (3000/8000, perfil Privado), tarefa agendada de inicialização, plano de energia, horário ativo do Windows Update. Exigem privilégio de administrador do Windows e serão executadas pelo usuário ou com autorização explícita.
- **Rede**: reserva DHCP no roteador da loja (feita pelo usuário).
- **Dependências**: Git for Windows (novo). Nenhuma dependência Python nova.
- **Dados**: nenhum impacto no Xano. Os dois ambientes compartilham o mesmo backend (risco aceito e registrado acima).
- **Riscos**:
  - fotos enviadas em `uploaded_files/` ficam em pastas diferentes por ambiente, e uma foto enviada em um não aparece no outro;
  - se o IP reservado mudar, é preciso recompilar a produção, porque o `api_url` é gravado no frontend na compilação;
  - o PWA no iPhone continua limitado por não haver HTTPS.
- **Documentação**: README (execução, ambientes e atualização).
