## Context

O envio pelo SendGrid já existe em `harley_store/email_clientes.py`: `_agendar` dispara em segundo plano e devolve False sem configuração, e `_enviar` registra no log as recusas. As contas são criadas em `UsuariosState.salvar`, via `xano_admin_client.criar_usuario`, que levanta exceção quando o Xano recusa. Hoje o rodapé do modelo HTML diz sempre "porque é cliente".

## Goals / Non-Goals

**Goals:**
- Reaproveitar o envio e o modelo visual existentes, sem nova configuração.

**Non-Goals:**
- Renomear o módulo `email_clientes.py`: o nome continua válido para a maior parte do conteúdo, e trocá-lo mexeria em imports e testes sem ganho.

## Decisions

### D1. Nova função `boas_vindas_conta(nome, email)` em `email_clientes.py`
Segue o padrão de `boas_vindas` e `parabens_compra`: monta os parágrafos com o nome escapado, a versão em texto simples e chama `_agendar`. Não recebe a senha, então ela não pode ir para o e-mail por engano.

### D2. Rodapé por parâmetro em `_modelo_html`
`_modelo_html(titulo, paragrafos, motivo=...)`, com o padrão "porque é cliente da loja", mantém iguais os e-mails de clientes e a ferramenta de teste. **Alternativa:** um segundo modelo HTML. Foi descartada porque duplicaria o layout.

### D3. Envio só depois de `criar_usuario` dar certo
A chamada fica depois do `await admin.criar_usuario(...)`, fora dos `except`. Se a criação falhar, nenhum e-mail sai. `atualizar_email`, `definir_perfil` e `salvar_senha` não chamam o envio.

## Risks / Trade-offs

- [O e-mail chega antes de a pessoa receber a senha] → o texto avisa que a senha é entregue pessoalmente por um administrador.
- [E-mail digitado errado pelo administrador] → a mensagem vai para outra pessoa sem dado sensível, porque não leva a senha nem o endereço do sistema.
