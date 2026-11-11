## 1. Regras compartilhadas

- [x] 1.1 Criar `validacao.py` com CPF, CNPJ, e-mail, telefone, números e imagens; feito em 24/09/2026 (commit `018aba5`) e verificado pelos testes `test_cpf`, `test_cnpj`, `test_mensagens_e_formato`, `test_email_e_telefone`, `test_numero` e `test_inteiro`
- [x] 1.2 Conferir as imagens pela extensão, tamanho e conteúdo; verificado pelos testes `test_aceita_imagem_real`, `test_recusa_extensao_e_conteudo_falso`, `test_recusa_arquivo_grande` e `test_respeita_extensoes_da_tela`

## 2. Telas

- [x] 2.1 Usar as regras em Clientes (CPF/CNPJ, e-mail, telefone e duplicidade) e Fornecedores (CNPJ e duplicidade); verificado no código de `clientes_state.py` e `fornecedores_state.py`
- [x] 2.2 Conferir placa, chassi, RENAVAM, ano, quilometragem, cilindrada, preços e datas nos cadastros de motos; verificado no código de `motos_loja_state.py` e `motos_state.py`
- [x] 2.3 Conferir nome, estoque e preço em Produtos; verificado no código de `produtos_state.py`
- [x] 2.4 Rodar os testes automáticos; verificado em 07/10/2026 (44 testes passando)
