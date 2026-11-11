## Context

Motivação em proposal.md. As motos da loja guardam a foto como objeto de imagem do Xano (`foto`), e as motos dos clientes como texto (`imagem`). Registro retroativo: o código já existia em 07/10/2026.

## Goals / Non-Goals

**Goals:**
- Foto para o maior número de motos sem enviar arquivos ao Xano.
- Nenhuma foto errada.

**Non-Goals:**
- Foto por cor da moto.
- Gravar a foto oficial no cadastro da moto.

## Decisions

### D1. Arquivos no app e mapa de modelos
As imagens ficam em `assets/motos/<modelo>.jpg`, servidas pelo próprio app. `fotos_oficiais.MODELOS` lista as palavras de cada modelo, o arquivo e a cilindrada de fábrica, do mais específico para o mais geral.
- *Alternativa:* enviar as fotos ao Xano. Rejeitada: ocuparia o armazenamento do plano Free para imagens que são iguais para todas as unidades.

### D2. Comparação por palavras inteiras
O nome do modelo é normalizado (sem acentos, minúsculas, pontuação vira espaço) e a busca exige as palavras inteiras do modelo da lista. Assim, "Harley-Davidson Fat Boy 114" encontra "fat boy", mas "Low Rider ST" não encontra "low rider s".

### D3. Foto oficial calculada na exibição
A foto oficial é decidida na hora de montar a tela (`foto_url` ou `imagem_url` com a oficial como alternativa), e nada é gravado no banco. O indicador `foto_oficial` muda o enquadramento (inteira, fundo branco) e o texto de ajuda.

### D4. Origem das imagens
Oito fotos vieram do site oficial atual; as da Iron 883 (2022) e da Street Glide Special (2023), que saíram de linha, vieram da versão arquivada do site oficial (Wayback Machine).

## Risks / Trade-offs

- [Modelos fora da lista ficam sem foto] → Para incluir um modelo, basta salvar a foto em `assets/motos/` e acrescentar uma linha em `fotos_oficiais.py` (documentado no README).
- [Cor da foto pode ser diferente da moto] → A foto representa o modelo, não a unidade; a loja pode enviar a foto real.
