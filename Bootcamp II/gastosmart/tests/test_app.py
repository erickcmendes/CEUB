"""Testes do app focados em delegação para `services`."""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import app  # noqa: E402, I001


def test_adicionar_gasto_delega_para_services():
    fake_services = MagicMock()
    fake_services.adicionar_gasto.return_value = {
        "id": 1,
        "descricao": "Almoço",
        "valor": 35.5,
        "categoria": "Alimentação",
    }

    with patch.object(app, "services", fake_services):
        gasto = app.adicionar_gasto("Almoço", 35.5, "Alimentação")

    fake_services.adicionar_gasto.assert_called_once_with("Almoço", 35.5, "Alimentação", None)
    assert gasto["id"] == 1


def test_listar_gastos_delega_para_services():
    fake_services = MagicMock()
    fake_services.listar_gastos.return_value = [{"id": 1, "descricao": "Teste"}]

    with patch.object(app, "services", fake_services):
        gastos = app.listar_gastos()

    fake_services.listar_gastos.assert_called_once_with()
    assert len(gastos) == 1


def test_remover_gasto_delega_para_services():
    fake_services = MagicMock()
    fake_services.remover_gasto.return_value = True

    with patch.object(app, "services", fake_services):
        resultado = app.remover_gasto(7)

    fake_services.remover_gasto.assert_called_once_with(7)
    assert resultado is True


def test_resumo_gastos_delega_para_services():
    fake_services = MagicMock()
    fake_services.resumo_gastos.return_value = {"total": 10.0, "por_categoria": {"Lazer": 10.0}}

    with patch.object(app, "services", fake_services):
        resumo = app.resumo_gastos()

    fake_services.resumo_gastos.assert_called_once_with()
    assert resumo["total"] == 10.0


