# Project Overview — Harley Store

Projeto acadêmico desenvolvido por **Marcelo** e **Daniel**.

## 1. Visão geral

O Harley Store é um sistema web de gestão para uma loja e oficina de motos
Harley-Davidson. Ele reúne em um só lugar o estoque de produtos e de motos,
as vendas no balcão, as ordens de serviço da oficina, as compras de
fornecedores, o cadastro de clientes e o acompanhamento financeiro da loja.

## 2. Problema

Uma loja que vende motos, peças e acessórios e que também mantém oficina
costuma controlar cada parte do negócio de forma separada (planilhas,
cadernos, anotações). Isso gera:

- estoque que não bate com o que foi vendido ou usado na oficina;
- dificuldade de saber quanto a loja faturou no dia e no mês;
- histórico de clientes e de suas motos espalhado;
- vendas apagadas ou alteradas sem rastro.

## 3. Objetivos

- Manter o estoque de produtos e de motos sempre correto, com histórico de
  cada entrada e saída.
- Registrar vendas, ordens de serviço e compras de forma rastreável (vendas
  são canceladas, nunca apagadas).
- Mostrar a situação financeira da loja: faturamento do dia e do mês,
  separado entre motos e produtos, incluindo a mão de obra.
- Permitir o uso pelos funcionários na rede da loja, inclusive pelo celular.

## 4. Público-alvo / usuários

| Usuário | O que faz no sistema |
|---|---|
| **Administrador** (dono/gerente) | Tudo o que o funcionário faz, mais criar e gerenciar as contas de acesso. |
| **Funcionário** (vendedor, mecânico) | Opera o dia a dia: vendas, ordens de serviço, compras, cadastros e consulta ao painel. |
| **Cliente da loja** | Não acessa o sistema; recebe e-mails (boas-vindas, parabéns pela compra de moto e confirmação de pagamento) e, quando paga por boleto ou cartão, a cobrança do Asaas por e-mail e SMS. |

Cada conta de acesso nova recebe um e-mail de boas-vindas no e-mail cadastrado (sem a senha, que é entregue pessoalmente).

## 5. Escopo

**Dentro do escopo:**

- cadastros: clientes e suas motos, produtos, motos da loja, fornecedores,
  funcionários e contas de usuário;
- operações: vendas no balcão (com forma de pagamento e cobrança por boleto
  ou cartão pelo Asaas), ordens de serviço, compras de fornecedores;
- controle de estoque com histórico de movimentações;
- painel financeiro e impressão de documentos;
- e-mails automáticos aos clientes.

**Fora do escopo:**

- emissão de nota fiscal e integração com órgãos fiscais;
- loja virtual para o público;
- cobrança pelo Asaas em produção (por enquanto, só no ambiente Sandbox),
  parcelamento e estorno pelo sistema;
- cadastro público de usuários (só o administrador cria contas);
- controle contábil completo (contas a pagar/receber).

## 6. Principais funcionalidades

- **Painel:** estoque de motos e de produtos, faturamento do dia e do mês
  (motos × produtos, com mão de obra), gráfico dos últimos 12 meses,
  estoque baixo e ordens de serviço em aberto.
- **Produtos:** catálogo separado em abas por categoria e uma aba **Motos**
  com o estoque de motos à venda.
- **Clientes e motos dos clientes:** cadastro e vínculo cliente → moto, com
  a foto oficial do modelo.
- **Vendas / Balcão:** venda com vários itens (produtos, mão de obra e uma
  moto da loja, com preço e dados do cadastro), baixa de estoque na hora e
  cancelamento com devolução ao estoque. A moto vendida passa para as
  motos do cliente. Na conclusão, o funcionário escolhe a forma de
  pagamento: na loja, boleto, cartão de crédito ou "cliente escolhe"; as
  três últimas geram a cobrança no Asaas, que o cliente recebe por e-mail e
  SMS, e a confirmação do pagamento aparece na venda.
- **Ordens de serviço:** peças usadas e mão de obra; ao concluir, o valor
  entra no faturamento do dia.
- **Compras:** entrada de mercadoria de fornecedores, somando no estoque.
- **Impressão:** comprovante de venda, ordem de serviço, entrada de
  mercadoria e ficha/recibo da moto em A4.
- **E-mails:** boas-vindas ao cliente cadastrado, parabéns a quem compra
  uma moto, confirmação de pagamento das vendas cobradas pelo Asaas e
  boas-vindas a quem ganha uma conta de acesso ao sistema.

## 7. Requisitos e restrições importantes

- O estoque nunca pode ficar negativo, e toda alteração de saldo deixa
  registro.
- Vendas não são apagadas, apenas canceladas, e a venda cancelada sai do
  faturamento.
- Um cadastro em uso (ex.: cliente com vendas) não pode ser excluído.
- Dados como CPF/CNPJ, placa, chassi, e-mail e telefone são validados.
- O banco de dados (Xano) está no plano gratuito, que tem limite de
  requisições, e é o mesmo para desenvolvimento e produção.
- Dia e mês do faturamento seguem o fuso de São Paulo.

## 8. Arquitetura tecnológica

- **Frontend:** Reflex. O Reflex será utilizado como tecnologia exclusiva
  para implementação do frontend da aplicação (interface e servidor da
  aplicação no mesmo projeto, em Python 3.12).
- **Ambiente:** `venv` nativo do Python + `pip`, com as dependências em
  `requirements.txt` (sem `uv`).
- **Banco de dados e autenticação:** **Xano** (API REST na nuvem). Não há
  banco local.
- **E-mails:** **SendGrid**.
- **Cobranças:** **Asaas** (Sandbox), API REST. O servidor consulta as
  cobranças em aberto periodicamente, porque fica na rede da loja e não
  recebe avisos da internet (webhook).
- **Execução:** servidor Windows na rede da loja; acesso pelo navegador do
  computador ou do celular.

## 9. Princípios de desenvolvimento

- Desenvolvimento incremental, uma mudança por vez, registrada no OpenSpec.
- Escopo enxuto: só o que foi combinado; nada de campos ou tabelas extras
  sem necessidade.
- Regras de negócio no servidor, com funções testáveis por testes
  automáticos.
- Interface e documentação em português do Brasil.

## 10. Segurança e integridade

- Toda tela e toda ação exigem login válido, conferido no servidor.
- Perfis de acesso (administrador/funcionário) conferidos também no Xano.
- A API de dados exige autenticação; o servidor usa uma conta de serviço
  cujas credenciais ficam fora do controle de versão (`.env`).
- Alterações de estoque protegidas contra operações simultâneas.

## 11. Estratégia de desenvolvimento

O sistema foi construído em fatias funcionais: primeiro os cadastros e as
vendas, depois a integridade do estoque e a segurança, em seguida as motos
da loja, as fotos, os e-mails e, por fim, o painel financeiro. Cada fatia
está registrada como uma change em `openspec/changes/archive/`.

## 12. Fonte de verdade e documentação

| Assunto | Onde está |
|---|---|
| Visão do projeto | este documento |
| Conceitos do domínio | `docs/domain-model.md` |
| Regras para agentes de IA | `AGENTS.md` |
| Comportamento consolidado do sistema | `openspec/specs/` |
| Histórico de mudanças | `openspec/changes/archive/` |
| Esquema real do banco | `xano/table/` |
| Instalação e operação | `README.md` |
