---
name: architecture
description: Este documento descreve os relacionamentos e a finalidade das tabelas criadas.
knowledge_type: doc
scope: workspace
inclusion: on demand
enabled: true
guid: quj1IFvmxZAdmtcFUKmJmgGz0Kg
---
# Documentação da Arquitetura do Banco de Dados

Este documento descreve os relacionamentos e a finalidade das tabelas criadas.

## Diagrama Lógico (Relacionamentos)

### Núcleo de Cadastro
- **Clientes**: Cadastro base de pessoas/empresas.
- **Motos_Clientes**: Relacionada a `Clientes` (1:N). Cada moto pertence a um cliente.
- **Funcionarios**: Cadastro de equipe (Vendedores e Mecânicos).
- **Fornecedores**: Cadastro de parceiros comerciais.

### Fluxo de Estoque
- **Produtos**: Peças e mercadorias.
- **Entrada_Mercadoria**: Cabeçalho de notas de compra de fornecedores. Relacionada a `Fornecedores`.
- **Itens_Compra_Estoque**: Detalhes dos produtos comprados. Relacionada a `Entrada_Mercadoria` e `Produtos`.

### Operações e Vendas
- **Transacoes**: Registro central de vendas (Motos, Peças, OS). Relacionada a `Funcionarios`, `Clientes` (opcional) e `Motos_Clientes` (opcional).
- **Ordens_Servico**: Controle de oficina. Relacionada a `Motos_Clientes` (veículo) e `Funcionarios` (mecânico).
- **Itens_Ordem_Servico**: Peças/Serviços usados na OS. Relacionada a `Ordens_Servico` e `Produtos`.

## Como Expandir
Para adicionar uma nova funcionalidade (ex: Controle de Garantia):
1. Crie a tabela `/table/garantias.xs` com a FK `id_moto_cliente`.
2. Crie uma função `/function/garantia/verificar_status.xs`.
3. Adicione o endpoint correspondente em `/api/oficina/garantia_GET.xs`.
