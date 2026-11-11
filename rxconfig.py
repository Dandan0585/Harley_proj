import reflex as rx

# Endereço e portas NÃO ficam aqui: cada ambiente os define por variáveis
# de ambiente REFLEX_* antes de iniciar (o Reflex as aplica por cima desta
# configuração). Não coloque o IP da loja neste arquivo, porque ele é
# versionado e compartilhado pelos dois ambientes.
#   - desenvolvimento: scripts/iniciar_dev.ps1      -> http://localhost:3001
#   - produção:        scripts/iniciar_producao.ps1 -> http://<IP>:3000
#     (o IP fica em producao.local.ps1, fora do git)
config = rx.Config(
    app_name="harley_store",
    # Sem banco local: todos os dados ficam no Xano (harley_store/xano_client.py).
    # None é obrigatório: sem esta linha o Reflex usaria "sqlite:///reflex.db"
    # e o `reflex run` pararia pedindo `reflex db init`.
    db_url=None,
    tailwind=None,
)
