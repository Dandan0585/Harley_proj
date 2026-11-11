"""
Validações e conversões de campos de formulário, usadas por todos os states.

Tudo aqui roda no SERVIDOR (dentro dos event handlers), então vale mesmo
que alguém mande dados direto pelo websocket, sem passar pela tela.

As funções `validar_*` devolvem "" quando o valor é válido, ou a mensagem
pronta para mostrar ao funcionário.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Formatos de imagem aceitos: extensão -> (MIME, assinaturas do início do arquivo).
# A assinatura é conferida porque a extensão sozinha não garante o conteúdo.
IMAGENS_PERMITIDAS: dict[str, tuple[str, tuple[bytes, ...]]] = {
    ".png": ("image/png", (b"\x89PNG\r\n\x1a\n",)),
    ".jpg": ("image/jpeg", (b"\xff\xd8\xff",)),
    ".jpeg": ("image/jpeg", (b"\xff\xd8\xff",)),
    ".webp": ("image/webp", (b"RIFF",)),
    ".gif": ("image/gif", (b"GIF87a", b"GIF89a")),
}
TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024  # 5 MB


def somente_digitos(texto: str | None) -> str:
    return re.sub(r"\D", "", texto or "")


def _digito_verificador(numeros: str, pesos: list[int]) -> int:
    resto = sum(int(n) * p for n, p in zip(numeros, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    d = somente_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    dv1 = _digito_verificador(d[:9], list(range(10, 1, -1)))
    dv2 = _digito_verificador(d[:10], list(range(11, 1, -1)))
    return d[9:] == f"{dv1}{dv2}"


def cnpj_valido(cnpj: str) -> bool:
    d = somente_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = _digito_verificador(d[:12], pesos1)
    dv2 = _digito_verificador(d[:13], [6, *pesos1])
    return d[12:] == f"{dv1}{dv2}"


def formatar_cpf_cnpj(doc: str) -> str:
    """Grava sempre no mesmo formato, para a busca e a checagem de duplicidade
    não dependerem de como o funcionário digitou."""
    d = somente_digitos(doc)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return (doc or "").strip()


def validar_cpf_cnpj(doc: str) -> str:
    d = somente_digitos(doc)
    if len(d) == 11:
        return "" if cpf_valido(d) else "CPF inválido: confira os números digitados."
    if len(d) == 14:
        return "" if cnpj_valido(d) else "CNPJ inválido: confira os números digitados."
    return "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos)."


def validar_cnpj(doc: str) -> str:
    return "" if cnpj_valido(doc) else "CNPJ inválido: informe os 14 dígitos corretamente."


def validar_email(email: str) -> str:
    """Campo opcional: vazio é válido."""
    email = (email or "").strip()
    if not email:
        return ""
    return "" if _EMAIL.match(email) else "E-mail inválido (exemplo: nome@empresa.com.br)."


def validar_telefone(telefone: str) -> str:
    """Campo opcional: vazio é válido. Aceita fixo (10) ou celular (11) com DDD."""
    d = somente_digitos(telefone)
    if not d:
        return ""
    return "" if len(d) in (10, 11) else "Telefone inválido: informe o DDD e o número (10 ou 11 dígitos)."


def formatar_telefone(telefone: str) -> str:
    d = somente_digitos(telefone)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return (telefone or "").strip()


def numero(texto: str | float | int | None) -> float:
    """Aceita "150000", "150.000,00", "150000.50" e "R$ 1.234,56".
    Levanta ValueError se não for número."""
    if isinstance(texto, (int, float)):
        return float(texto)
    t = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t) if t else 0.0


def inteiro(texto: str | int | None) -> int:
    """Número inteiro; aceita "1.500" (milhar) mas recusa "1,5". Levanta ValueError."""
    if isinstance(texto, int):
        return texto
    t = (texto or "").strip().replace(".", "").replace(" ", "")
    return int(t) if t else 0


def moeda(valor: float) -> str:
    """1234.5 -> "1.234,50" (formato brasileiro)."""
    return f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def validar_imagem(nome_arquivo: str, conteudo: bytes, extensoes: set[str] | None = None) -> tuple[str, str]:
    """Devolve (erro, mime). Confere extensão, tamanho e a assinatura do arquivo."""
    from pathlib import Path

    extensao = Path(nome_arquivo or "").suffix.lower()
    aceitas = extensoes or set(IMAGENS_PERMITIDAS)
    if extensao not in aceitas or extensao not in IMAGENS_PERMITIDAS:
        nomes = ", ".join(sorted(e.lstrip(".").upper() for e in aceitas if e != ".jpeg"))
        return f"Formato inválido. Use {nomes}.", ""
    if not conteudo:
        return "O arquivo está vazio.", ""
    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        return "Imagem muito grande (máximo 5 MB).", ""
    mime, assinaturas = IMAGENS_PERMITIDAS[extensao]
    if not any(conteudo.startswith(a) for a in assinaturas) or (
        extensao == ".webp" and conteudo[8:12] != b"WEBP"
    ):
        return "O arquivo não é uma imagem válida (o conteúdo não corresponde à extensão).", ""
    return "", mime
