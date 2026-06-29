"""
Camada de repositório para a tabela `gastos` no Supabase.

Isola o acesso ao banco do restante da aplicação. Todas as funções aceitam
um `client` opcional para facilitar testes com mock.
"""

from typing import Optional

try:
    from .config import get_supabase_client
except ImportError:  # pragma: no cover - fallback for direct script imports in tests
    from config import get_supabase_client

TABELA = "gastos"


def inserir(gasto: dict, client: Optional[object] = None) -> dict:
    """
    Insere um gasto e retorna o registro criado (com `id` gerado pelo banco).

    Args:
        gasto: dicionário com `descricao`, `valor`, `categoria` e opcionalmente `data`.
        client: cliente Supabase. Se None, usa o cliente padrão do ambiente.

    Returns:
        Registro inserido (dict) ou {} se a inserção não retornar dados.
    """
    cli = client or get_supabase_client()
    resposta = cli.table(TABELA).insert(gasto).execute()
    dados = resposta.data or []
    return dados[0] if dados else {}


def listar(client: Optional[object] = None) -> list[dict]:
    """
    Retorna todos os gastos cadastrados, ordenados por data (mais recente primeiro).
    """
    cli = client or get_supabase_client()
    resposta = cli.table(TABELA).select("*").order("data", desc=True).execute()
    return resposta.data or []


def remover_por_id(gasto_id: int, client: Optional[object] = None) -> bool:
    """
    Remove um gasto pelo `id`.

    Returns:
        True se ao menos um registro foi removido, False caso contrário.
    """
    cli = client or get_supabase_client()
    resposta = cli.table(TABELA).delete().eq("id", gasto_id).execute()
    return bool(resposta.data)
