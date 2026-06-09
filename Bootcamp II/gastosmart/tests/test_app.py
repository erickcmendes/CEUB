"""Testes do app focados em delegação para `services` e clima."""

import os
import sys
import urllib.error  # noqa: F401
from unittest.mock import MagicMock, patch

import pytest

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


# ─── Testes de integração: buscar_clima ───────────────────────────────────────

def _mock_openweather_response(cidade="Brasilia", temp=28.5, descricao="céu limpo"):
    """Monta um mock da resposta JSON da API OpenWeather."""
    json_bytes = (
        f'{{"name":"{cidade}",'
        f'"main":{{"temp":{temp}}},'
        f'"weather":[{{"description":"{descricao}"}}]}}'
    ).encode()

    mock_response = MagicMock()
    mock_response.read.return_value = json_bytes
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def test_buscar_clima_retorna_dados_corretos():
    """
    Teste de integração: valida que buscar_clima processa corretamente
    a resposta da API OpenWeather (usando mock para não depender da rede).
    """
    mock_resp = _mock_openweather_response("Brasilia", 28.5, "céu limpo")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        resultado = app.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is not None
    assert resultado["cidade"] == "Brasilia"
    assert resultado["temperatura"] == 28.5
    assert resultado["descricao"] == "Céu limpo"


def test_buscar_clima_sem_api_key_retorna_none():
    """Sem chave de API configurada, deve retornar None sem chamar a rede."""
    resultado = app.buscar_clima("Brasilia", "")
    assert resultado is None


def test_buscar_clima_erro_de_rede_retorna_none():
    """Se a API estiver indisponível, deve retornar None sem lançar exceção."""
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        resultado = app.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is None


def test_buscar_clima_resposta_invalida_retorna_none():
    """Se a API retornar JSON inesperado, deve retornar None."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"{}"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        resultado = app.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is None
