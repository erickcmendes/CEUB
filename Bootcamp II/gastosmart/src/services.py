from datetime import date
from typing import List, Dict, Any

CATEGORIAS = ["Alimentação", "Transporte", "Saúde", "Lazer", "Educação", "Moradia", "Outros"]

try:
    from . import repository
except ImportError:  
    import repository


def adicionar_gasto(descricao: str, valor: float, categoria: str, data: str | None = None) -> Dict[str, Any]:
    if not descricao or not descricao.strip():
        raise ValueError("A descrição não pode ser vazia.")
    if valor <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    if categoria not in CATEGORIAS:
        raise ValueError(f"Categoria inválida. Escolha entre: {', '.join(CATEGORIAS)}")

    gasto = {
        "descricao": descricao.strip(),
        "valor": round(valor, 2),
        "categoria": categoria,
        "data": data or str(date.today()),
    }

    return repository.inserir(gasto)


def listar_gastos(client: object | None = None) -> List[Dict[str, Any]]:
    return repository.listar(client=client)


def remover_gasto(gasto_id: int, client: object | None = None) -> bool:
    return repository.remover_por_id(gasto_id, client=client)


def resumo_gastos(client: object | None = None) -> Dict[str, Any]:
    gastos = listar_gastos(client=client)
    total = sum(g["valor"] for g in gastos)
    por_categoria: dict = {}
    for g in gastos:
        cat = g["categoria"]
        por_categoria[cat] = round(por_categoria.get(cat, 0) + g["valor"], 2)
    return {"total": round(total, 2), "por_categoria": por_categoria}