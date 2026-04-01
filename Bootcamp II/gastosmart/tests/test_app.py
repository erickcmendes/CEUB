"""
Testes automatizados do GastoSmart
Execução: pytest tests/
"""

import os
import sys

import pytest

# Ajusta o path para importar o módulo src/app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import app  # noqa: E402, I001


# ─── Fixture: arquivo de dados temporário ─────────────────────────────────────

@pytest.fixture(autouse=True)
def arquivo_temporario(tmp_path, monkeypatch):
    """Redireciona o DATA_FILE para um arquivo temporário em cada teste."""
    arquivo = tmp_path / "gastos_test.json"
    monkeypatch.setattr(app, "DATA_FILE", str(arquivo))


# ─── Testes: adicionar_gasto ───────────────────────────────────────────────────

def test_adicionar_gasto_valido():
    """Caminho feliz: adicionar um gasto válido."""
    gasto = app.adicionar_gasto("Almoço", 35.50, "Alimentação")
    assert gasto["id"] == 1
    assert gasto["descricao"] == "Almoço"
    assert gasto["valor"] == 35.50
    assert gasto["categoria"] == "Alimentação"


def test_adicionar_gasto_incrementa_id():
    """IDs devem ser incrementados a cada novo gasto."""
    g1 = app.adicionar_gasto("Uber", 20.0, "Transporte")
    g2 = app.adicionar_gasto("Cinema", 45.0, "Lazer")
    assert g2["id"] == g1["id"] + 1


def test_adicionar_gasto_descricao_vazia_levanta_erro():
    """Descrição vazia deve lançar ValueError."""
    with pytest.raises(ValueError, match="descrição não pode ser vazia"):
        app.adicionar_gasto("", 10.0, "Outros")


def test_adicionar_gasto_valor_negativo_levanta_erro():
    """Valor negativo deve lançar ValueError."""
    with pytest.raises(ValueError, match="maior que zero"):
        app.adicionar_gasto("Mercado", -50.0, "Alimentação")


def test_adicionar_gasto_valor_zero_levanta_erro():
    """Valor zero deve lançar ValueError."""
    with pytest.raises(ValueError, match="maior que zero"):
        app.adicionar_gasto("Mercado", 0, "Alimentação")


def test_adicionar_gasto_categoria_invalida_levanta_erro():
    """Categoria inexistente deve lançar ValueError."""
    with pytest.raises(ValueError, match="Categoria inválida"):
        app.adicionar_gasto("Teste", 10.0, "CategoriaNãoExiste")


# ─── Testes: listar_gastos ────────────────────────────────────────────────────

def test_listar_gastos_vazio():
    """Lista deve ser vazia quando não há gastos."""
    assert app.listar_gastos() == []


def test_listar_gastos_retorna_todos():
    """Listar deve retornar todos os gastos adicionados."""
    app.adicionar_gasto("Farmácia", 60.0, "Saúde")
    app.adicionar_gasto("Curso Python", 120.0, "Educação")
    gastos = app.listar_gastos()
    assert len(gastos) == 2


# ─── Testes: remover_gasto ────────────────────────────────────────────────────

def test_remover_gasto_existente():
    """Remover um gasto existente deve retornar True."""
    gasto = app.adicionar_gasto("Gasolina", 80.0, "Transporte")
    resultado = app.remover_gasto(gasto["id"])
    assert resultado is True
    assert app.listar_gastos() == []


def test_remover_gasto_inexistente():
    """Tentar remover ID que não existe deve retornar False."""
    resultado = app.remover_gasto(9999)
    assert resultado is False


def test_remover_nao_afeta_outros_gastos():
    """Remover um gasto não deve remover os demais."""
    g1 = app.adicionar_gasto("Aluguel", 800.0, "Moradia")
    g2 = app.adicionar_gasto("Netflix", 45.0, "Lazer")
    app.remover_gasto(g1["id"])
    gastos = app.listar_gastos()
    assert len(gastos) == 1
    assert gastos[0]["id"] == g2["id"]


# ─── Testes: resumo_gastos ────────────────────────────────────────────────────

def test_resumo_sem_gastos():
    """Resumo com lista vazia deve retornar total zero."""
    resumo = app.resumo_gastos()
    assert resumo["total"] == 0
    assert resumo["por_categoria"] == {}


def test_resumo_total_correto():
    """Total deve ser a soma de todos os valores."""
    app.adicionar_gasto("Pão", 5.0, "Alimentação")
    app.adicionar_gasto("Ônibus", 4.50, "Transporte")
    resumo = app.resumo_gastos()
    assert resumo["total"] == 9.50


def test_resumo_por_categoria():
    """Totais por categoria devem estar corretos."""
    app.adicionar_gasto("Almoço", 30.0, "Alimentação")
    app.adicionar_gasto("Jantar", 40.0, "Alimentação")
    app.adicionar_gasto("Uber", 15.0, "Transporte")
    resumo = app.resumo_gastos()
    assert resumo["por_categoria"]["Alimentação"] == 70.0
    assert resumo["por_categoria"]["Transporte"] == 15.0
