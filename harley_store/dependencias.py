"""
Integridade referencial na exclusão.

O Xano (plano Free) não tem chaves estrangeiras entre as tabelas: nada
impede apagar um cliente que tem vendas, e o histórico fica apontando para
um id que não existe mais (registro órfão). Toda exclusão de cadastro passa
por `em_uso()`, que procura o registro nas tabelas que o referenciam.

Para uma tabela nova que aponte para outra, acrescente a linha em REFERENCIAS.
"""

from __future__ import annotations

from . import xano_client as xano

# tabela referenciada -> [(tabela que aponta, campo com o id, nome para o usuário)]
REFERENCIAS: dict[str, list[tuple[str, str, str]]] = {
    "clientes": [
        ("motos_clientes", "id_cliente", "motos de clientes"),
        ("transacoes", "id_cliente", "vendas"),
        ("motos", "cliente_id", "motos da loja"),
    ],
    "fornecedores": [
        ("entrada_mercadoria", "id_fornecedor", "compras"),
    ],
    "funcionarios": [
        ("transacoes", "id_funcionario", "vendas"),
        ("ordens_servico", "id_funcionario", "ordens de serviço"),
    ],
    "motos": [
        ("itens_transacao", "moto_id", "vendas"),
    ],
    "motos_clientes": [
        ("ordens_servico", "id_moto_cliente", "ordens de serviço"),
        ("transacoes", "id_moto_cliente", "vendas"),
    ],
    "produtos": [
        ("itens_transacao", "produto_id", "vendas"),
        ("itens_ordem_servico", "id_produto", "ordens de serviço"),
        ("itens_compra_estoque", "id_produto", "compras"),
    ],
}


async def em_uso(tabela: str, registro_id: int) -> list[str]:
    """Nomes (para o usuário) das tabelas onde o registro é usado. Vazio = pode excluir.
    Erros de conexão sobem: na dúvida, a exclusão não acontece."""
    registro_id = int(registro_id)
    usos = []
    for tabela_ref, campo, nome in REFERENCIAS.get(tabela, []):
        if any(int(r.get(campo) or 0) == registro_id for r in await xano.listar(tabela_ref)):
            usos.append(nome)
    return usos


def mensagem_em_uso(descricao: str, usos: list[str]) -> str:
    return f"Não é possível excluir {descricao}: há registros ligados a ele em {', '.join(usos)}."
