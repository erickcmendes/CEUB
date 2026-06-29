"""Testes da camada de serviços com `repository` mockado e clima opcional."""

import os
import sys
import urllib.error
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
    fake_repository.listar.return_value = [
        {
            "id": 1,
            "descricao": "A",
            "valor": 5.0,
            "categoria": "Outros",
            "data": "2026-06-09"
        }
    ]

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
        {
            "id": 1,
            "descricao": "A",
            "valor": 10.0,
            "categoria": "Alimentação",
            "data": "2026-06-01"
        },
        {
            "id": 2,
            "descricao": "B",
            "valor": 5.0,
            "categoria": "Alimentação",
            "data": "2026-06-02"
        },
        {
            "id": 3,
            "descricao": "C",
            "valor": 2.5,
            "categoria": "Lazer",
            "data": "2026-06-03"
        }
    ]

    with patch.object(services, "repository", fake_repository):
        resumo = services.resumo_gastos()

    fake_repository.listar.assert_called_once_with(client=None)
    assert resumo["total"] == 17.5
    assert resumo["por_categoria"]["Alimentação"] == 15.0
    assert resumo["por_categoria"]["Lazer"] == 2.5


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
    mock_resp = _mock_openweather_response("Brasilia", 28.5, "céu limpo")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        resultado = services.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is not None
    assert resultado["cidade"] == "Brasilia"
    assert resultado["temperatura"] == 28.5
    assert resultado["descricao"] == "Céu limpo"


def test_buscar_clima_sem_api_key_retorna_none():
    resultado = services.buscar_clima("Brasilia", "")
    assert resultado is None


def test_buscar_clima_erro_de_rede_retorna_none():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        resultado = services.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is None


def test_buscar_clima_resposta_invalida_retorna_none():
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"{}"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        resultado = services.buscar_clima("Brasilia", "fake-api-key")

    assert resultado is None

def test_resumo_gastos_sem_dados():
    fake_repository = MagicMock()
    fake_repository.listar.return_value = []

    with patch.object(services, "repository", fake_repository):
        resumo = services.resumo_gastos()

    assert resumo["total"] == 0
    assert resumo["por_categoria"] == {}


def test_resumo_gastos_categoria_unica():
    fake_repository = MagicMock()
    fake_repository.listar.return_value = [
        {
            "id": 1,
            "descricao": "Mercado",
            "valor": 100.0,
            "categoria": "Alimentação",
            "data": "2026-06-10",
        }
    ]

    with patch.object(services, "repository", fake_repository):
        resumo = services.resumo_gastos()

    assert resumo["total"] == 100.0
    assert resumo["por_categoria"]["Alimentação"] == 100.0


def test_listar_gastos_retorna_lista_vazia():
    fake_repository = MagicMock()
    fake_repository.listar.return_value = []

    with patch.object(services, "repository", fake_repository):
        gastos = services.listar_gastos()

    assert gastos == []
    
