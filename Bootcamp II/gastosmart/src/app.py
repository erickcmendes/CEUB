"""
GastoSmart - Gerenciador de Gastos Pessoais
Versão: 1.0.0
"""

import json
import os
from datetime import date

# Caminho do arquivo de dados
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "gastos.json")

CATEGORIAS = ["Alimentação", "Transporte", "Saúde", "Lazer", "Educação", "Moradia", "Outros"]


# ─── Funções de Persistência ───────────────────────────────────────────────────

def carregar_gastos() -> list:
    """Carrega os gastos do arquivo JSON. Retorna lista vazia se não existir."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_gastos(gastos: list) -> None:
    """Salva a lista de gastos no arquivo JSON."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(gastos, f, ensure_ascii=False, indent=2)


# ─── Funções de Negócio ────────────────────────────────────────────────────────

def adicionar_gasto(descricao: str, valor: float, categoria: str, data: str = None) -> dict:
    """
    Adiciona um novo gasto à lista e salva.
    Retorna o gasto criado.
    """
    if not descricao or not descricao.strip():
        raise ValueError("A descrição não pode ser vazia.")
    if valor <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    if categoria not in CATEGORIAS:
        raise ValueError(f"Categoria inválida. Escolha entre: {', '.join(CATEGORIAS)}")

    gastos = carregar_gastos()

    novo_id = (max(g["id"] for g in gastos) + 1) if gastos else 1

    gasto = {
        "id": novo_id,
        "descricao": descricao.strip(),
        "valor": round(valor, 2),
        "categoria": categoria,
        "data": data or str(date.today()),
    }

    gastos.append(gasto)
    salvar_gastos(gastos)
    return gasto


def listar_gastos() -> list:
    """Retorna todos os gastos cadastrados."""
    return carregar_gastos()


def remover_gasto(gasto_id: int) -> bool:
    """
    Remove um gasto pelo ID.
    Retorna True se removido, False se não encontrado.
    """
    gastos = carregar_gastos()
    novos_gastos = [g for g in gastos if g["id"] != gasto_id]

    if len(novos_gastos) == len(gastos):
        return False  # Nenhum item foi removido

    salvar_gastos(novos_gastos)
    return True


def resumo_gastos() -> dict:
    """
    Calcula o total geral e o total por categoria.
    Retorna um dicionário com 'total' e 'por_categoria'.
    """
    gastos = carregar_gastos()
    total = sum(g["valor"] for g in gastos)

    por_categoria = {}
    for g in gastos:
        cat = g["categoria"]
        por_categoria[cat] = round(por_categoria.get(cat, 0) + g["valor"], 2)

    return {"total": round(total, 2), "por_categoria": por_categoria}


# ─── Interface CLI ─────────────────────────────────────────────────────────────

def exibir_menu():
    print("\n" + "=" * 40)
    print("       💸 GastoSmart v1.0.0")
    print("=" * 40)
    print("  [1] Adicionar gasto")
    print("  [2] Listar gastos")
    print("  [3] Remover gasto")
    print("  [4] Ver resumo")
    print("  [0] Sair")
    print("=" * 40)


def input_valor(prompt: str) -> float:
    """Solicita um valor numérico ao usuário com validação."""
    while True:
        try:
            valor = float(input(prompt).replace(",", "."))
            if valor <= 0:
                print("❌ O valor deve ser maior que zero.")
            else:
                return valor
        except ValueError:
            print("❌ Digite um número válido.")


def input_categoria() -> str:
    """Exibe as categorias e retorna a escolhida."""
    print("\nCategorias disponíveis:")
    for i, cat in enumerate(CATEGORIAS, 1):
        print(f"  [{i}] {cat}")
    while True:
        try:
            escolha = int(input("Escolha o número da categoria: "))
            if 1 <= escolha <= len(CATEGORIAS):
                return CATEGORIAS[escolha - 1]
            print("❌ Opção inválida.")
        except ValueError:
            print("❌ Digite um número.")


def tela_adicionar():
    print("\n── Adicionar Gasto ──")
    descricao = input("Descrição: ")
    valor = input_valor("Valor (R$): ")
    categoria = input_categoria()

    try:
        gasto = adicionar_gasto(descricao, valor, categoria)
        print(f"\n✅ Gasto adicionado! ID #{gasto['id']} — {gasto['descricao']}"
              f" — R$ {gasto['valor']:.2f}")
    except ValueError as e:
        print(f"\n❌ Erro: {e}")


def tela_listar():
    gastos = listar_gastos()
    print("\n── Lista de Gastos ──")
    if not gastos:
        print("Nenhum gasto cadastrado ainda.")
        return
    print(f"{'ID':<5} {'Data':<12} {'Categoria':<15} {'Descrição':<25} {'Valor':>10}")
    print("-" * 70)
    for g in gastos:
        linha = (
            f"{g['id']:<5} {g['data']:<12} {g['categoria']:<15}"
            f" {g['descricao']:<25} R$ {g['valor']:>8.2f}"
        )
        print(linha)


def tela_remover():
    print("\n── Remover Gasto ──")
    try:
        gasto_id = int(input("Digite o ID do gasto a remover: "))
        if remover_gasto(gasto_id):
            print(f"✅ Gasto #{gasto_id} removido com sucesso.")
        else:
            print(f"❌ Gasto #{gasto_id} não encontrado.")
    except ValueError:
        print("❌ ID inválido.")


def tela_resumo():
    resumo = resumo_gastos()
    print("\n── Resumo de Gastos ──")
    print(f"{'Total geral:':<20} R$ {resumo['total']:.2f}")
    if resumo["por_categoria"]:
        print("\nPor categoria:")
        for cat, valor in sorted(resumo["por_categoria"].items(), key=lambda x: -x[1]):
            print(f"  {cat:<18} R$ {valor:.2f}")
    else:
        print("Nenhum gasto registrado.")


def main():
    """Ponto de entrada da aplicação."""
    print("Bem-vindo ao GastoSmart! 💰")
    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            tela_adicionar()
        elif opcao == "2":
            tela_listar()
        elif opcao == "3":
            tela_remover()
        elif opcao == "4":
            tela_resumo()
        elif opcao == "0":
            print("\nAté logo! 👋")
            break
        else:
            print("❌ Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
