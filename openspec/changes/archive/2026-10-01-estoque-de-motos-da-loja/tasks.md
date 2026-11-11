## 1. Banco de dados (Xano)

- [x] 1.1 Criar em `motos` os campos `renavam`, `cilindrada`, `localizacao` e `fotos` e o endpoint `motos/foto`; feito em 24/09/2026 e verificado no espelho `xano/table/motos.xs` e em `xano/api/harley/motos/foto_POST.xs`

## 2. Tela

- [x] 2.1 Implementar as sete situações com cor, ícone e texto, e a regra de que só Vendida sai do estoque; feito em 24/09/2026 (commit `018aba5`) e verificado no código de `motos_loja_state.py` e `pages/motos_loja.py`
- [x] 2.2 Acrescentar RENAVAM, cilindrada, localização com sugestões e as fotos adicionais com galeria; verificado no código
- [x] 2.3 Gravar sempre o registro completo; verificado no código (`salvar` envia todos os campos, incluindo `foto` e `fotos`)
- [x] 2.4 Tornar o chassi opcional até a venda e exigir chassi e cliente para Vendida; feito em 01/10/2026 (commit `cb9b8ff`) e verificado no código (`_validar` aceita chassi vazio e exige chassi e cliente para Vendida); a tela foi usada de 05 a 07/10/2026 para cadastrar 12 motos

## 3. Catálogo

- [x] 3.1 Criar `scripts/cadastrar_motos_catalogo.py` com prévia, confirmação e sem repetir modelos; feito em 01/10/2026 e verificado no código; em 07/10/2026 o script ainda não tinha cadastrado nenhuma moto no Xano (não há moto sem chassi no estoque)
- [x] 3.2 Compilar o app e rodar os testes; verificado em 07/10/2026 (`reflex compile` sem erros e 44 testes passando)
