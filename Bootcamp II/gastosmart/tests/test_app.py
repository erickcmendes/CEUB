"""
Testes automatizados do GastoSmart
Execução: pytest tests/
"""

import os
import sys
import urllib.error  # noqa: F401
from unittest.mock import MagicMock, patch

import pytest

# Ajusta o path para importar o módulo src/app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import app  # noqa: E402, I001


# ─── Fixture: arquivo de dados temporário ─────────────────────────────────────

@pytest.fixture(autouse=True)
def arquivo_temporario(tmp_path, monkeypatch):
    """Redireciona o DATA_FILE para um arquivo temporário em cada teste."""
    arquivo = tmp_path / "gastos_test.json"
    monkeypatch.delenv("GASTOSMART_DATA_FILE", raising=False)
    monkeypatch.setattr(app, "DATA_FILE", str(arquivo))
    return arquivo


# ─── Testes unitários: persistência ─────────────────────────────────

def test_carregar_gastos_arquivo_corrompido_retorna_lista_vazia(arquivo_temporario):
    """Arquivo JSON inválido não deve derrubar a aplicação."""
    arquivo_temporario.write_text("{json-invalido", encoding="utf-8")

    assert app.carregar_gastos() == []


def test_carregar_gastos_formato_invalido_retorna_lista_vazia(arquivo_temporario):
    """A persistência local espera uma lista de gastos."""
    arquivo_temporario.write_text('{"id": 1}', encoding="utf-8")

    assert app.carregar_gastos() == []


def test_salvar_gastos_respeita_caminho_por_variavel_de_ambiente(tmp_path, monkeypatch):
    """GASTOSMART_DATA_FILE permite configurar o arquivo local de dados."""
    arquivo_customizado = tmp_path / "ambiente" / "gastos.json"
    monkeypatch.setenv("GASTOSMART_DATA_FILE", str(arquivo_customizado))

    app.salvar_gastos([{"id": 1, "descricao": "Teste", "valor": 10.0}])

    assert arquivo_customizado.exists()
    assert app.carregar_gastos()[0]["descricao"] == "Teste"


# ─── Testes unitários: adicionar_gasto ────────────────────────────────────────

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


# ─── Testes unitários: listar_gastos ──────────────────────────────────────────

def test_listar_gastos_vazio():
    """Lista deve ser vazia quando não há gastos."""
    assert app.listar_gastos() == []


def test_listar_gastos_retorna_todos():
    """Listar deve retornar todos os gastos adicionados."""
    app.adicionar_gasto("Farmácia", 60.0, "Saúde")
    app.adicionar_gasto("Curso Python", 120.0, "Educação")
    gastos = app.listar_gastos()
    assert len(gastos) == 2


# ─── Testes unitários: remover_gasto ──────────────────────────────────────────

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


# ─── Testes unitários: resumo_gastos ──────────────────────────────────────────

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
