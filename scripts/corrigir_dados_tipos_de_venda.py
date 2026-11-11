"""
Correções de dados da change tipos-de-venda-coerentes (OpenSpec), aprovadas
pelo grupo no Explore de 09/10/2026:

1. Cancela a "venda" nº 8 (tipo COMPRA, R$ 22.000): na verdade a loja comprou
   a Low Rider S usada da cliente Helena. Vendas não são apagadas, só
   canceladas; a venda já estava fora do faturamento.
2. Cadastra essa Low Rider S (placa HIJ8K90) em Produtos > Motos: Em
   preparação, preço de compra R$ 22.000,00, entrada em 15/02/2026. Ano, cor
   e quilometragem não são conhecidos e ficam em branco.
3. Corrige o preço de compra da moto da loja nº 15 (Low Rider S 2026) de
   R$ 119,95 para R$ 119.950,00.

Uso (PowerShell, na pasta do projeto):
    .venv\\Scripts\\python.exe scripts\\corrigir_dados_tipos_de_venda.py

Mostra o que vai fazer e só grava depois de você digitar "s". Pode rodar de
novo sem medo: cada correção confere o estado atual e é pulada se já foi
feita, ou se o registro não for o esperado.
"""

from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harley_store import vendas_servico  # noqa: E402
from harley_store import xano_client as xano  # noqa: E402  (carrega o .env)

USUARIO = "Correção de dados (change tipos-de-venda-coerentes)"

VENDA_ID = 8
MOTIVO = "Compra da moto da cliente Helena registrada em Produtos > Motos"

PLACA, CHASSI = "HIJ8K90", "9BW12345678901238"
MOTO_HELENA = {
    "marca": "Harley-Davidson",
    "modelo": "Low Rider S",
    "ano": 0,             # não informado (a tela grava 0 quando o ano fica em branco)
    "cor": "",
    "placa": PLACA,
    "chassi": CHASSI,
    "quilometragem": 0,
    "status": "Em preparação",
    "em_estoque": True,   # "Em preparação" não tira a moto do estoque
    "preco_compra": 22000.0,
    "preco_venda": 0,
    # mesmo cálculo da tela (motos_loja_state._input_para_epoch)
    "data_entrada": xano.datetime_para_epoch_ms(datetime.datetime(2026, 2, 15)),
    "data_saida": 0,
    "observacoes": ("Comprada da cliente Helena Castro Silveira em 15/02/2026 (corrige o lançamento "
                    "nº 8, registrado como venda). Ano, cor e quilometragem não informados."),
    "cliente_id": 0,
    "foto": None,         # a tela mostra a foto oficial do modelo
    "fotos": None,
    "renavam": "",
    "cilindrada": None,   # depende do ano, que não é conhecido
    "localizacao": "",
}

MOTO_15_ID, PRECO_ERRADO, PRECO_CERTO = 15, 119.95, 119950.0


def _so_letras_e_numeros(texto) -> str:
    return "".join(c for c in str(texto or "").upper() if c.isalnum())


async def planejar() -> list[tuple[str, str]]:
    """[(acao, descricao)]; acao = "fazer" | "feito" | "parar"."""
    venda, motos, moto_15 = await asyncio.gather(
        xano.buscar_direto("transacoes", VENDA_ID), xano.listar("motos"), xano.buscar_direto("motos", MOTO_15_ID))
    plano = []

    if venda is None:
        plano.append(("parar", f"Venda nº {VENDA_ID} não existe."))
    elif vendas_servico.esta_cancelada(venda):
        plano.append(("feito", f"Venda nº {VENDA_ID} já está cancelada."))
    elif (venda.get("tipo_transacao") or "").upper() != "COMPRA" or float(venda.get("valor_total") or 0) != 22000:
        plano.append(("parar", f"Venda nº {VENDA_ID} não é a COMPRA de R$ 22.000 esperada; nada será feito com ela."))
    else:
        plano.append(("fazer", f"Cancelar a venda nº {VENDA_ID} (COMPRA, R$ 22.000) com o motivo: {MOTIVO}"))

    repetida = next((m for m in motos if _so_letras_e_numeros(m.get("placa")) == PLACA
                     or _so_letras_e_numeros(m.get("chassi")) == CHASSI), None)
    if repetida:
        plano.append(("feito", f"Moto da loja com a placa {PLACA} já existe (nº {repetida['id']})."))
    else:
        plano.append(("fazer", f"Cadastrar em Produtos > Motos a Low Rider S {PLACA}: Em preparação, "
                               "compra R$ 22.000,00, entrada 15/02/2026, ano/cor/km em branco"))

    if moto_15 is None:
        plano.append(("parar", f"Moto da loja nº {MOTO_15_ID} não existe."))
    elif float(moto_15.get("preco_compra") or 0) == PRECO_CERTO:
        plano.append(("feito", f"Moto nº {MOTO_15_ID} já está com preço de compra R$ 119.950,00."))
    elif float(moto_15.get("preco_compra") or 0) != PRECO_ERRADO or "LOW RIDER S" != (moto_15.get("modelo") or "").upper():
        plano.append(("parar", f"Moto nº {MOTO_15_ID} não é a Low Rider S com R$ 119,95 esperada; nada será feito com ela."))
    else:
        plano.append(("fazer", f"Corrigir o preço de compra da moto nº {MOTO_15_ID} (Low Rider S 2026): "
                               "R$ 119,95 -> R$ 119.950,00"))
    return plano


async def aplicar() -> None:
    venda = await xano.buscar_direto("transacoes", VENDA_ID)
    if venda and not vendas_servico.esta_cancelada(venda) and (venda.get("tipo_transacao") or "").upper() == "COMPRA":
        resultado = await vendas_servico.cancelar_venda(VENDA_ID, MOTIVO, USUARIO)
        print(f"  venda nº {VENDA_ID}: {resultado['situacao']} {resultado['mensagem']}".rstrip())
        await asyncio.sleep(2.5)  # folga para o limite de requisições do Xano Free

    motos = await xano.listar("motos")
    if not any(_so_letras_e_numeros(m.get("placa")) == PLACA or _so_letras_e_numeros(m.get("chassi")) == CHASSI
               for m in motos):
        nova = await xano.criar("motos", MOTO_HELENA)
        print(f"  moto da Helena cadastrada: nº {nova['id']}")
        await asyncio.sleep(2.5)

    moto_15 = await xano.buscar_direto("motos", MOTO_15_ID)
    if moto_15 and float(moto_15.get("preco_compra") or 0) == PRECO_ERRADO:
        dados = {k: v for k, v in moto_15.items() if k != "id"}  # PATCH do Xano exige o registro completo
        dados["preco_compra"] = PRECO_CERTO
        await xano.atualizar("motos", MOTO_15_ID, dados)
        print(f"  moto nº {MOTO_15_ID}: preço de compra corrigido para R$ 119.950,00")


async def main() -> None:
    plano = await planejar()
    marcas = {"fazer": "+ fazer ", "feito": "= feito ", "parar": "! parado"}
    for acao, descricao in plano:
        print(f"  {marcas[acao]}  {descricao}")
    if not any(acao == "fazer" for acao, _ in plano):
        print("Nada a corrigir.")
        return
    if input("\nAplicar as correções marcadas com + no Xano? [s/N] ").strip().lower() != "s":
        print("Cancelado; nada foi gravado.")
        return
    await aplicar()
    print("\nResultado:")
    for acao, descricao in await planejar():
        print(f"  {marcas[acao]}  {descricao}")


if __name__ == "__main__":
    asyncio.run(main())
