## Why

Os formulários aceitavam CPF e CNPJ inválidos, placas e chassis em qualquer formato, valores negativos e arquivos que não eram imagens. Documentos digitados com e sem pontuação passavam como diferentes, o que deixava cadastrar o mesmo cliente duas vezes.

Registro retroativo: implementado na auditoria de 24/09/2026 (commit `018aba5`). Esta change documenta o comportamento em uso.

## What Changes

- CPF e CNPJ conferidos pelos dígitos verificadores, gravados sempre no mesmo formato e com duplicidade conferida pelos números.
- E-mail e telefone (opcionais) conferidos e o telefone gravado formatado.
- Placa (antiga ou Mercosul), chassi, RENAVAM, ano, quilometragem e cilindrada conferidos nos cadastros de motos.
- Valores aceitos no formato brasileiro, sem negativos e com limite máximo.
- Imagens conferidas pela extensão, pelo tamanho (até 5 MB) e pelo conteúdo do arquivo.

## Capabilities

### New Capabilities
- `cadastros/validacao-de-dados`: regras de validação e formatação dos dados digitados nos cadastros.

### Modified Capabilities
<!-- Nenhuma. -->

## Impact

- **Código**: `harley_store/validacao.py` (funções compartilhadas) e os states de clientes, fornecedores, produtos, motos da loja, motos de clientes e usuários.
- **Testes**: `tests/test_validacao.py`.
- **Dados**: registros antigos não são alterados; a regra vale a partir da próxima gravação de cada um.
