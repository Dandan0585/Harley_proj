"""
Fotos oficiais dos modelos Harley-Davidson (assets/motos/), tiradas do site
harley-davidson.com: foto de perfil de fábrica de cada modelo.

A foto é escolhida pelo NOME DO MODELO gravado no cadastro (motos da loja e
motos dos clientes). Moto sem modelo reconhecido não ganha foto: nada é
inventado. Uma foto enviada pelo funcionário sempre tem prioridade.

Para incluir um modelo novo: salve a foto em assets/motos/<arquivo>.jpg e
acrescente uma linha em MODELOS (o mais específico primeiro).
"""

from __future__ import annotations

import re
import unicodedata

# (palavras do modelo, arquivo em assets/motos, cilindrada oficial em cm³)
# A ordem importa: "street glide special" precisa vir antes de um eventual
# "street glide", "road glide limited" antes de "road glide", etc.
MODELOS: list[tuple[str, str, int]] = [
    ("iron 883", "iron-883", 883),
    ("fat boy", "fat-boy", 1868),
    ("heritage classic", "heritage-classic", 1868),
    ("sportster s", "sportster-s", 1252),
    ("pan america 1250 special", "pan-america-1250-special", 1252),
    ("street glide special", "street-glide-special", 1868),
    ("road glide limited", "road-glide-limited", 1868),
    ("low rider s", "low-rider-s", 1923),
    ("breakout", "breakout", 1923),
    ("nightster special", "nightster-special", 975),
]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " " + re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip() + " "


def _modelo(modelo: str) -> tuple[str, str, int] | None:
    nome = _normalizar(modelo)
    return next((m for m in MODELOS if f" {m[0]} " in nome), None)


def foto_oficial(modelo: str) -> str:
    """Endereço da foto oficial do modelo (ex.: "/motos/fat-boy.jpg") ou ""."""
    encontrado = _modelo(modelo)
    return f"/motos/{encontrado[1]}.jpg" if encontrado else ""


def modelo_oficial(modelo: str) -> str:
    """Nome do modelo reconhecido (ex.: "fat boy") ou "" — para comparar cadastros."""
    encontrado = _modelo(modelo)
    return encontrado[0] if encontrado else ""


def cilindrada_oficial(modelo: str) -> int:
    encontrado = _modelo(modelo)
    return encontrado[2] if encontrado else 0
