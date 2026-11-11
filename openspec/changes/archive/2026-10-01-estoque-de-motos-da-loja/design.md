## Context

Motivação em proposal.md. A tabela `motos` do Xano é separada de `motos_clientes`. O PATCH do Xano substitui o registro inteiro, e `foto` é um campo de imagem do Xano (objeto com `path` e `url`), não um texto. Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Retratar as situações reais de uma concessionária sem perder dados ao editar.

**Non-Goals:**
- Ligar a venda da moto a uma venda em `transacoes` (a venda é registrada na própria moto).
- Bloquear a exclusão de moto vendida.

## Decisions

### D1. Situação em texto e `em_estoque` derivado
O campo `status` guarda a situação; `em_estoque` é gravado como "situação diferente de Vendida". Uma situação nova é só acrescentar à lista `STATUS_OPCOES` e ao mapa visual da página.

### D2. Registro completo em toda gravação
`salvar()` monta todos os campos, incluindo o objeto da foto já existente (guardado em `_foto`) e a lista `fotos`, para o PATCH não apagar nada.

### D3. Fotos no armazenamento do Xano
Cada imagem é enviada pelo endpoint `POST motos/foto` e o objeto devolvido é gravado em `foto` (principal) ou na lista `fotos` (adicionais).

### D4. Chassi opcional até a venda
A validação aceita chassi vazio; a situação Vendida exige chassi e cliente. A checagem de duplicidade ignora placa e chassi vazios.

### D5. Script do catálogo sem placa nem chassi
`scripts/cadastrar_motos_catalogo.py` compara os modelos pelo nome reconhecido (`fotos_oficiais.modelo_oficial`), mostra a prévia e só grava depois de confirmação. As placas e os chassis da lista original pertencem às motos dos clientes; repeti-los faria a mesma moto existir duas vezes.

## Risks / Trade-offs

- [Preço de venda é o valor da venda] → Se a venda for negociada por outro valor, o preço de venda precisa ser atualizado antes de marcar Vendida (o painel e o recibo usam esse campo).
- [Fotos excluídas continuam no armazenamento do Xano] → O plano não oferece exclusão de arquivo pela API; registrado no README.
