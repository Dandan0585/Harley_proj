"""Testes das validações de formulário (rodam sem internet).

    .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import unittest

from harley_store import validacao as v


class TestDocumentos(unittest.TestCase):
    def test_cpf(self):
        self.assertTrue(v.cpf_valido("529.982.247-25"))
        self.assertTrue(v.cpf_valido("52998224725"))
        self.assertFalse(v.cpf_valido("529.982.247-24"))   # dígito errado
        self.assertFalse(v.cpf_valido("111.111.111-11"))   # repetido
        self.assertFalse(v.cpf_valido("123"))

    def test_cnpj(self):
        self.assertTrue(v.cnpj_valido("11.222.333/0001-81"))
        self.assertFalse(v.cnpj_valido("11.222.333/0001-80"))
        self.assertFalse(v.cnpj_valido("00.000.000/0000-00"))

    def test_mensagens_e_formato(self):
        self.assertEqual(v.validar_cpf_cnpj("52998224725"), "")
        self.assertIn("CPF inválido", v.validar_cpf_cnpj("52998224700"))
        self.assertIn("11 dígitos", v.validar_cpf_cnpj("1234"))
        self.assertEqual(v.formatar_cpf_cnpj("52998224725"), "529.982.247-25")
        self.assertEqual(v.formatar_cpf_cnpj("11222333000181"), "11.222.333/0001-81")

    def test_email_e_telefone(self):
        self.assertEqual(v.validar_email(""), "")
        self.assertEqual(v.validar_email("ana@loja.com.br"), "")
        self.assertNotEqual(v.validar_email("ana@loja"), "")
        self.assertEqual(v.validar_telefone("(11) 91234-5678"), "")
        self.assertNotEqual(v.validar_telefone("1234"), "")
        self.assertEqual(v.formatar_telefone("11912345678"), "(11) 91234-5678")


class TestNumeros(unittest.TestCase):
    def test_numero(self):
        self.assertEqual(v.numero("150.000,50"), 150000.5)
        self.assertEqual(v.numero("R$ 1.234,56"), 1234.56)
        self.assertEqual(v.numero("99.9"), 99.9)
        self.assertEqual(v.numero(""), 0.0)
        with self.assertRaises(ValueError):
            v.numero("abc")

    def test_inteiro(self):
        self.assertEqual(v.inteiro("1.500"), 1500)
        self.assertEqual(v.inteiro(""), 0)
        with self.assertRaises(ValueError):
            v.inteiro("1,5")


class TestImagem(unittest.TestCase):
    PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    JPG = b"\xff\xd8\xff\xe0" + b"0" * 100

    def test_aceita_imagem_real(self):
        self.assertEqual(v.validar_imagem("moto.png", self.PNG), ("", "image/png"))
        self.assertEqual(v.validar_imagem("moto.JPG", self.JPG), ("", "image/jpeg"))

    def test_recusa_extensao_e_conteudo_falso(self):
        self.assertIn("Formato inválido", v.validar_imagem("virus.exe", self.PNG)[0])
        self.assertIn("não é uma imagem", v.validar_imagem("falsa.png", b"MZ\x90\x00" + b"0" * 50)[0])
        self.assertIn("vazio", v.validar_imagem("vazia.png", b"")[0])

    def test_recusa_arquivo_grande(self):
        grande = self.PNG + b"0" * v.TAMANHO_MAXIMO_IMAGEM
        self.assertIn("muito grande", v.validar_imagem("grande.png", grande)[0])

    def test_respeita_extensoes_da_tela(self):
        gif = b"GIF89a" + b"0" * 10
        self.assertIn("Formato inválido", v.validar_imagem("a.gif", gif, {".png", ".jpg"})[0])


if __name__ == "__main__":
    unittest.main()
