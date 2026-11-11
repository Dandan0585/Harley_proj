## Context

Hoje o Balcão (`state/vendas_state.py` e `pages/vendas.py`) só monta itens de produtos (`produto_id`) e itens avulsos (`produto_id = 0`). As regras de registro e cancelamento ficam em `vendas_servico.py`. A moto da loja (tabela `motos`) é vendida pelo cadastro: `MotosLojaState.salvar` marca a moto como Vendida e envia o e-mail de parabéns. O Painel (`dashboard_state.lancamentos_faturamento`) conta essa moto em Motos pelo `preco_venda`, na `data_saida`, e conta todo item de venda em Produtos. Se a moto virasse um item avulso, ela seria contada duas vezes. A moto do cliente (tabela `motos_clientes`) exige placa e chassi, e os dois são únicos.

## Goals / Non-Goals

**Goals:**
- Vender uma moto da loja pelo Balcão, com o preço e os dados vindos do cadastro.
- A moto conta uma única vez no Painel, e o cancelamento desfaz a venda da moto.
- O comprador fica com a moto cadastrada em Motos dos clientes.

**Non-Goals:**
- Preço negociado no Balcão, mais de uma moto por venda e mudanças na venda pelo cadastro da moto.

## Decisions

### D1. Campo `moto_id` em `itens_transacao` (aprovado pelo grupo)
O item da moto é gravado com `produto_id = 0`, a descrição com os dados da moto, quantidade 1 e `moto_id` = id da moto da loja. **Alternativa:** ligar pelo chassi (`transacoes.id_moto_cliente` → `motos_clientes.chassi` → `motos.chassi`), sem campo novo. Foi descartada porque o vínculo seria indireto: um chassi corrigido depois ou uma moto sem cadastro de cliente quebrariam o Painel e o cancelamento. Como o Xano ignora em silêncio um campo que não existe, o servidor confere antes da venda se os itens já têm o campo (`moto_id` presente nos registros lidos), e confere depois se o item gravado voltou com o `moto_id`. Se faltar, a venda de moto é recusada, ou desfeita, com o pedido de aplicar `scripts/aplicar_xano.ps1`.

### D2. A moto conta no Painel pelo próprio cadastro
A venda marca a moto como Vendida, com `data_saida` = momento da venda. Assim a regra atual do Painel (moto Vendida, `preco_venda`, `data_saida`) passa a contar também a venda do Balcão. Em `lancamentos_faturamento`, um item com `moto_id` é ignorado. **Alternativa:** contar o item e deixar de contar a moto pelo cadastro. Foi descartada porque mudaria a regra das motos vendidas por Produtos > Motos, e um preço editado depois no cadastro ficaria fora do Painel.

### D3. Preço e dados conferidos no servidor
`registrar_venda` recebe o item com `id_moto` e não usa a descrição nem o valor vindos da tela. O servidor relê a moto direto no Xano (`buscar_direto`) e monta o item com `preco_venda`, quantidade 1 e a descrição feita por `descricao_moto()`. A moto é recusada quando está Vendida ou Indisponível, quando não tem chassi (ele vai no recibo, como já exige o cadastro) ou quando não tem preço de venda. A tela usa as mesmas funções puras para avisar antes.

### D4. Ordem das gravações e compensação
Toda a venda com moto roda dentro de uma trava por moto (`asyncio.Lock`, como as travas de estoque e de venda), para que uma venda simultânea da mesma moto releia a situação já Vendida. A ordem é:
1. baixar o estoque dos produtos;
2. criar a venda;
3. gravar os itens;
4. marcar a moto como Vendida.

Uma falha nos passos 2 a 4 devolve o estoque e deixa a venda cancelada com o motivo de falha, como já acontece hoje. Os passos seguintes não desfazem a venda e só geram avisos: cadastrar a moto do cliente, ligar a venda a esse cadastro (`id_moto_cliente`), enviar o e-mail de parabéns e gravar o histórico de estoque. Para devolver os avisos, `registrar_venda` passa a retornar `(id_da_venda, avisos)`.

### D5. Cadastro em Motos dos clientes
O cadastro da moto do cliente procura em `motos_clientes` um registro com o mesmo chassi. Se encontrar, troca o dono para o comprador e mantém a foto e a placa. Se não encontrar, cria o registro com o modelo da moto, para manter a foto oficial, além da placa e do chassi. Uma moto sem placa (0 km) não pode ser cadastrada, porque a placa é obrigatória e única: a venda segue, com o aviso para cadastrar a moto depois do emplacamento. Uma placa já usada por outro chassi também gera aviso.

### D6. Cancelamento devolve a moto
Em `cancelar_venda`, depois de marcar a venda como cancelada (mesma ordem do design D4 da change de cancelamento), cada item com `moto_id` devolve a moto:
- a moto volta a Em estoque, com `em_estoque` verdadeiro, sem cliente e sem data de saída. Isso só acontece se ela ainda estiver Vendida para o mesmo cliente; se não estiver, o sistema avisa para conferir;
- o cadastro em Motos dos clientes ligado à venda é excluído se tiver o mesmo chassi e não tiver ordens de serviço. Se tiver, ele é mantido, e o sistema avisa para conferir.

### D7. Exclusão protegida da moto da loja
`dependencias.REFERENCIAS["motos"]` passa a incluir `itens_transacao.moto_id` (vendas), e `MotosLojaState.excluir` passa a usar `em_uso`, como os outros cadastros.

## Risks / Trade-offs

- [O grupo ainda não aplicou o campo no Xano] → a venda de moto é recusada antes de mexer em qualquer coisa, com o aviso de qual script rodar; as demais vendas seguem normais.
- [A trava por moto vale só dentro de um processo do servidor] → é a mesma limitação das travas de estoque; a loja roda um único processo.
- [Cadastro do cliente transferido de um dono anterior com ordens de serviço] → as ordens de serviço continuam ligadas à moto, que agora mostra o novo dono; no cancelamento o cadastro não é apagado e o sistema pede conferência.

## Migration Plan

1. O grupo roda `.\scripts\aplicar_xano.ps1`, confere a prévia (campo `moto_id` e os 2 endpoints) e confirma.
2. Publicar o código.
3. Teste com uma moto marcada como TESTE: vender pelo Balcão, conferir o Painel, Motos dos clientes e o comprovante, cancelar a venda e conferir que a moto voltou ao estoque. Ao final, remover os registros de TESTE.

**Para desfazer:** reverter o commit. O campo `moto_id` pode ficar no Xano, porque é opcional e não atrapalha.
