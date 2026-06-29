"""
GastoSmart - Gerenciador de Gastos Pessoais
Versão: 1.1.0
"""

import os

try:
    from . import services
except ImportError:
    import services

CATEGORIAS = ["Alimentação", "Transporte", "Saúde", "Lazer", "Educação", "Moradia", "Outros"]

def adicionar_gasto(descricao: str, valor: float, categoria: str, data: str | None = None) -> dict:
    """Encaminha a operação para `services` para manter compatibilidade."""
    return services.adicionar_gasto(descricao, valor, categoria, data)


def listar_gastos() -> list:
    """Encaminha a operação para `services` para manter compatibilidade."""
    return services.listar_gastos()


def remover_gasto(gasto_id: int) -> bool:
    """Encaminha a operação para `services` para manter compatibilidade."""
    return services.remover_gasto(gasto_id)


def resumo_gastos() -> dict:
    """Encaminha a operação para `services` para manter compatibilidade."""
    return services.resumo_gastos()


# ─── Interface CLI ─────────────────────────────────────────────────────────────

def exibir_menu():
    print("\n" + "=" * 40)
    print("       💸 GastoSmart v1.1.0")
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
        gasto = services.adicionar_gasto(descricao, valor, categoria)
        print(
            f"\n✅ Gasto adicionado! ID #{gasto['id']}"
            f" — {gasto['descricao']}"
            f" — R$ {gasto['valor']:.2f}"
        )
    except ValueError as e:
        print(f"\n❌ Erro: {e}")


def tela_listar():
    gastos = services.listar_gastos()
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
        if services.remover_gasto(gasto_id):
            print(f"✅ Gasto #{gasto_id} removido com sucesso.")
        else:
            print(f"❌ Gasto #{gasto_id} não encontrado.")
    except ValueError:
        print("❌ ID inválido.")


def tela_resumo():
    resumo = services.resumo_gastos()
    print("\n── Resumo de Gastos ──")
    print(f"{'Total geral:':<20} R$ {resumo['total']:.2f}")
    if resumo["por_categoria"]:
        print("\nPor categoria:")
        for cat, valor in sorted(resumo["por_categoria"].items(), key=lambda x: -x[1]):
            print(f"  {cat:<18} R$ {valor:.2f}")
    else:
        print("Nenhum gasto registrado.")

    # Exibir clima se a chave da API estiver configurada
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    cidade = os.getenv("OPENWEATHER_CIDADE", "Brasilia")
    if api_key:
        print("\n── Clima Atual ──")
        clima = services.buscar_clima(cidade, api_key)
        if clima:
            print(f"  📍 {clima['cidade']}")
            print(f"  🌡️  {clima['temperatura']}°C — {clima['descricao']}")
        else:
            print("  ⚠️  Não foi possível obter o clima no momento.")


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
