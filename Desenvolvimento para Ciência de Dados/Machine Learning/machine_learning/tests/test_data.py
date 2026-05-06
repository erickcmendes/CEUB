"""
Testes básicos de smoke para o módulo de dados.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.preprocessor import (
    add_returns_column,
    drop_nulls,
    ensure_numeric,
)
import pandas as pd


def test_drop_nulls():
    df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})
    out = drop_nulls(df)
    assert len(out) == 2


def test_ensure_numeric():
    df = pd.DataFrame({"a": ["1", "2", "x"]})
    out = ensure_numeric(df, ["a"])
    assert out["a"].dtype.kind in "fi"


def test_add_returns_column():
    df = pd.DataFrame({"Close": [100, 110, 121]})
    out = add_returns_column(df, price_col="Close")
    assert "retorno" in out.columns
    assert pytest.approx(out["retorno"].iloc[1], rel=1e-6) == 0.10
