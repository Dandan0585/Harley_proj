---
name: AGENTS.md
description: Este workspace foi estruturado para ser modular e escalável, seguindo padrões de desenvolvimento em XanoScript.
knowledge_type: agents.md
scope: workspace
inclusion: on demand
enabled: true
guid: YxR7Vj4pSGmMQ41pE7f1ORbHg3g
---
# Diretrizes do Desenvolvedor - Concessionária e Oficina

Este workspace foi estruturado para ser modular e escalável, seguindo padrões de desenvolvimento em XanoScript.

## Arquitetura de Pastas
- `/table/`: Definições de esquema do banco de dados.
- `/api/{grupo}/`: Endpoints organizados por domínio (Relatórios, Vendas, Estoque).
- `/function/{categoria}/`: Lógica reutilizável (CRUD, Cálculos, Integrações).

## Convenções de Nomenclatura
- **Tabelas:** Plural e snake_case (ex: `motos_clientes`).
- **Funções:** Verbo + Substantivo (ex: `calculo/total_os`).
- **APIs:** Nome do recurso + Verbo HTTP no arquivo (ex: `resumo_GET.xs`).

## Regras de Expansão
1. **Novas Tabelas:** Sempre adicione um comentário no topo do arquivo `.xs` explicando o propósito da tabela.
2. **Lógica de Negócio:** Evite colocar lógica complexa diretamente nos Endpoints. Crie uma função em `/function/` e chame-a no Endpoint.
3. **Validação:** Use o bloco `precondition` nas funções para validar entradas antes de processar dados.
4. **Relacionamentos:** Use campos `int` com sufixo `_id` para chaves estrangeiras.

## Dicas para o VS Code
- Mantenha os arquivos `.xs` sincronizados usando a extensão Xano.
- Use comentários `//` para documentar cada passo do stack, facilitando a leitura visual no Xano dashboard.
