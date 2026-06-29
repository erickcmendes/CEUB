"""
Testes da camada de repositorio com o cliente Supabase mockado.
Estes testes NAO acessam a rede e nao dependem de credenciais.
"""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import repository  # noqa: E402, I001


def _client_mock(response_data=None):
    cli = MagicMock()
    dados = response_data if response_data is not None else []
    cli.table.return_value.insert.return_value.execute.return_value.data = dados
    (
        cli.table.return_value
        .select.return_value
        .order.return_value
        .execute.return_value.data
    ) = dados
    (
        cli.table.return_value
        .delete.return_value
        .eq.return_value
        .execute.return_value.data
    ) = dados
    return cli


def test_inserir_retorna_registro_criado():
    cli = _client_mock([
        {"id": 1, "descricao": "Cafe", "valor": 10.0, "categoria": "Alimentacao"}
    ])
    resultado = repository.inserir(
        {"descricao": "Cafe", "valor": 10.0, "categoria": "Alimentacao"},
        client=cli,
    )
    assert resultado["id"] == 1
    assert resultado["descricao"] == "Cafe"
    cli.table.assert_called_with("gastos")


def test_inserir_quando_resposta_vazia_devolve_dict_vazio():
    cli = _client_mock([])
    resultado = repository.inserir(
        {"descricao": "X", "valor": 5.0, "categoria": "Outros"},
        client=cli,
    )
    assert resultado == {}


def test_listar_retorna_lista_de_gastos():
    cli = _client_mock([
        {"id": 1, "descricao": "A", "valor": 10.0, "categoria": "Outros"},
        {"id": 2, "descricao": "B", "valor": 20.0, "categoria": "Lazer"},
    ])
    gastos = repository.listar(client=cli)
    assert len(gastos) == 2
    cli.table.assert_called_with("gastos")


def test_listar_sem_dados_retorna_lista_vazia():
    cli = _client_mock([])
    assert repository.listar(client=cli) == []


def test_listar_ordena_por_data_decrescente():
    cli = _client_mock([])
    repository.listar(client=cli)
    cli.table.return_value.select.return_value.order.assert_called_with("data", desc=True)


def test_remover_por_id_retorna_true_quando_remove_registro():
    cli = _client_mock([{"id": 5}])
    assert repository.remover_por_id(5, client=cli) is True


def test_remover_por_id_retorna_false_quando_nao_encontra():
    cli = _client_mock([])
    assert repository.remover_por_id(9999, client=cli) is False


def test_remover_por_id_filtra_pelo_id_correto():
    cli = _client_mock([{"id": 7}])
    repository.remover_por_id(7, client=cli)
    cli.table.return_value.delete.return_value.eq.assert_called_with("id", 7)
