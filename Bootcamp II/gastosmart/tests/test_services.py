"""Testes da camada de serviços com `repository` mockado."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import services  # noqa: E402, I001


def test_adicionar_gasto_valida_entradas():
    with pytest.raises(ValueError, match="descrição não pode ser vazia"):
        services.adicionar_gasto("", 10.0, "Alimentação")
    with pytest.raises(ValueError, match="maior que zero"):
        services.adicionar_gasto("Teste", 0, "Alimentação")
    with pytest.raises(ValueError, match="Categoria inválida"):
        services.adicionar_gasto("Teste", 10.0, "Inválida")


def test_adicionar_gasto_chama_repository():
    fake_repository = MagicMock()
    fake_repository.inserir.return_value = {
        "id": 1,
        "descricao": "Compra",
        "valor": 12.5,
        "categoria": "Outros",
        "data": "2026-06-09",
    }

    with patch.object(services, "repository", fake_repository):
        gasto = services.adicionar_gasto("Compra", 12.5, "Outros")

    fake_repository.inserir.assert_called_once()
    assert gasto["id"] == 1
    assert gasto["descricao"] == "Compra"


def test_listar_gastos_chama_repository():
    fake_repository = MagicMock()
    fake_repository.listar.return_value = [{"id": 1, "descricao": "A", "valor": 5.0, "categoria": "Outros"}]

    with patch.object(services, "repository", fake_repository):
        gastos = services.listar_gastos()

    fake_repository.listar.assert_called_once_with(client=None)
    assert len(gastos) == 1


def test_remover_gasto_chama_repository():
    fake_repository = MagicMock()
    fake_repository.remover_por_id.return_value = True

    with patch.object(services, "repository", fake_repository):
        resultado = services.remover_gasto(10)

    fake_repository.remover_por_id.assert_called_once_with(10, client=None)
    assert resultado is True


def test_resumo_gastos_agrega_por_categoria():
    fake_repository = MagicMock()
    fake_repository.listar.return_value = [
        {"id": 1, "descricao": "A", "valor": 10.0, "categoria": "Alimentação", "data": "2026-06-01"},
        {"id": 2, "descricao": "B", "valor": 5.0, "categoria": "Alimentação", "data": "2026-06-02"},
        {"id": 3, "descricao": "C", "valor": 2.5, "categoria": "Lazer", "data": "2026-06-03"},
    ]

    with patch.object(services, "repository", fake_repository):
        resumo = services.resumo_gastos()

    fake_repository.listar.assert_called_once_with(client=None)
    assert resumo["total"] == 17.5
    assert resumo["por_categoria"]["Alimentação"] == 15.0
    assert resumo["por_categoria"]["Lazer"] == 2.5