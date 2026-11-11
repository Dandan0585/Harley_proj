# clientes/emails-aos-clientes Specification

## Purpose
Envia aos clientes, em nome da loja, e-mails automáticos de boas-vindas no cadastro e de parabéns na compra de uma moto, sem que uma falha no envio atrapalhe o cadastro ou a venda.

## Requirements

### Requirement: E-mail de boas-vindas
Ao cadastrar um cliente novo com e-mail, o sistema SHALL enviar a ele um e-mail de boas-vindas em nome da loja, e a mensagem de confirmação do cadastro MUST informar que o e-mail foi enviado. Cliente sem e-mail e a edição de um cliente existente MUST NOT disparar o e-mail.

#### Scenario: Cliente novo com e-mail
- **WHEN** o funcionário cadastra um cliente com e-mail e o envio está configurado
- **THEN** o cadastro é salvo, aparece "E-mail de boas-vindas enviado." e o cliente recebe o e-mail de boas-vindas

#### Scenario: Cliente sem e-mail
- **WHEN** o funcionário cadastra um cliente sem e-mail
- **THEN** o cadastro é salvo e nenhum e-mail é enviado

### Requirement: E-mail de parabéns pela compra
Quando uma moto da loja for marcada como Vendida para um cliente com e-mail, o sistema SHALL enviar ao comprador um e-mail de parabéns com a descrição da moto (marca, modelo, ano e cor). Salvar de novo a mesma venda MUST NOT reenviar o e-mail; trocar o comprador de uma moto vendida MUST enviar ao novo comprador.

#### Scenario: Moto vendida
- **WHEN** o funcionário marca uma moto como Vendida para um cliente com e-mail
- **THEN** o cliente recebe "Parabéns pela sua <moto>!" e a tela informa que o e-mail de parabéns foi enviado

#### Scenario: Corrigir a observação de uma moto já vendida
- **WHEN** o funcionário edita só a observação de uma moto já vendida e salva
- **THEN** nenhum e-mail novo é enviado

### Requirement: Remetente e configuração
Os e-mails SHALL sair do endereço da loja configurado como remetente, com o nome da loja configurado (padrão "Harley Store"), e as respostas dos clientes MUST chegar a esse endereço. Sem a chave e o remetente configurados, o sistema MUST NOT enviar e-mails e MUST continuar funcionando normalmente.

#### Scenario: Envio não configurado
- **WHEN** um cliente com e-mail é cadastrado e a chave do SendGrid não está configurada
- **THEN** o cadastro é salvo normalmente, sem erro e sem e-mail

### Requirement: Envio sem atrapalhar a operação
O envio SHALL acontecer em segundo plano, sem fazer o funcionário esperar. Uma falha no envio MUST NOT desfazer o cadastro ou a venda, e MUST ser registrada no log.

#### Scenario: Serviço de e-mail recusa o envio
- **WHEN** o SendGrid recusa o envio de um e-mail
- **THEN** o cadastro ou a venda continuam gravados e o motivo da recusa fica no log

### Requirement: Conteúdo do e-mail
O e-mail SHALL ter a identidade visual da loja (preto e laranja) e uma versão em texto simples. Os dados do cliente MUST ser tratados como texto, nunca como código da mensagem.

#### Scenario: Nome com caracteres especiais
- **WHEN** o nome do cliente contém sinais como "<" e ">"
- **THEN** o nome aparece no e-mail como texto, sem alterar a formatação da mensagem

### Requirement: Verificação da configuração
O sistema SHALL oferecer uma ferramenta que confere se a chave e o remetente estão configurados, se a chave é aceita e tem permissão de envio e se o remetente está verificado, e que pode mandar um e-mail de teste. A chave MUST NOT ser exibida.

#### Scenario: Chave inválida
- **WHEN** a chave configurada não é aceita pelo SendGrid
- **THEN** a ferramenta informa que o SendGrid recusou a chave e não tenta enviar
