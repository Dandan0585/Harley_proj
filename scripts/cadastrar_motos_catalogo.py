"""
Cadastra no estoque da loja (tabela `motos` do Xano, aba Produtos > Motos)
os modelos Harley-Davidson do catálogo que ainda não estão lá.

Uso (PowerShell, na pasta do projeto):
    .venv\\Scripts\\python.exe scripts\\cadastrar_motos_catalogo.py

Mostra o que vai ser cadastrado e só grava depois de você digitar "s".
Pode rodar de novo sem medo: modelo que já existe no estoque é pulado.

Por que sem placa e sem chassi: as placas e chassis da lista original
(ABC1D23 / 9BW12345678901231...) são das motos dos CLIENTES (tabela
motos_clientes). Repeti-los aqui faria a mesma moto existir duas vezes,
como da loja e como do cliente. Cada modelo entra como unidade 0 km, com
a foto oficial e a cilindrada de fábrica; chassi, ano, cor e preços são
preenchidos pela equipe quando a unidade chegar. O chassi é exigido para
marcar a moto como Vendida.
"""

from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harley_store import xano_client as xano  # noqa: E402  (carrega o .env)
from harley_store.fotos_oficiais import cilindrada_oficial, modelo_oficial  # noqa: E402

MODELOS = [
    "Iron 883",
    "Fat Boy 114",
    "Heritage Classic",
    "Sportster S",
    "Pan America 1250 Special",
    "Street Glide Special",
    "Road Glide Limited",
    "Low Rider S",
    "Breakout 117",
    "Nightster Special",
]
OBSERVACAO = "Unidade 0 km do catálogo. Antes de vender: informar chassi, ano, cor e preços."


async def main() -> None:
    existentes = await xano.listar("motos")
    ja_no_estoque = {modelo_oficial(m.get("modelo") or "") for m in existentes} - {""}
    novos = [m for m in MODELOS if modelo_oficial(m) not in ja_no_estoque]

    print(f"Motos já no estoque: {len(existentes)}")
    for m in MODELOS:
        print(f"  {'+ cadastrar' if m in novos else '= já existe'}  Harley-Davidson {m}")
    if not novos:
        print("Nada a cadastrar.")
        return
    if input(f"\nCadastrar {len(novos)} moto(s) no Xano? [s/N] ").strip().lower() != "s":
        print("Cancelado; nada foi gravado.")
        return

    hoje = xano.datetime_para_epoch_ms(datetime.datetime.combine(datetime.date.today(), datetime.time()))
    for modelo in novos:
        await xano.criar("motos", {
            "marca": "Harley-Davidson",
            "modelo": modelo,
            "ano": 0,
            "cor": "",
            "placa": "",
            "chassi": "",
            "quilometragem": 0,
            "status": "Em estoque",
            "em_estoque": True,
            "preco_compra": 0,
            "preco_venda": 0,
            "data_entrada": hoje,
            "data_saida": 0,
            "observacoes": OBSERVACAO,
            "cliente_id": 0,
            "foto": None,     # a tela mostra a foto oficial do modelo (fotos_oficiais.py)
            "fotos": None,
            "renavam": "",
            "cilindrada": cilindrada_oficial(modelo),
            "localizacao": "Showroom",
        })
        print(f"  cadastrada: Harley-Davidson {modelo}")
        await asyncio.sleep(2.5)  # folga para o limite de requisições do Xano Free
    print("Pronto. Confira em Produtos > Motos (o app atualiza o cache em até 5 min, ou reinicie-o).")


if __name__ == "__main__":
    asyncio.run(main())
