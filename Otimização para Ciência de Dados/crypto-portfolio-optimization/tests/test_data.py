"""
# FR-05, NFR-01, NFR-05, D-004: Tests for data ingestion, validation and financial moments.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from portfolio_opt.data import (
    compute_file_sha256,
    verify_data_integrity,
    load_and_validate_prices,
    compute_returns_and_scenarios,
)


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Fixture providing a valid toy price CSV file."""
    csv_file = tmp_path / "toy_prices.csv"
    data = [
        {"date": "2024-01-01", "asset": "BTC", "close": 100.0},
        {"date": "2024-01-01", "asset": "ETH", "close": 10.0},
        {"date": "2024-01-02", "asset": "BTC", "close": 110.0},
        {"date": "2024-01-02", "asset": "ETH", "close": 12.0},
        {"date": "2024-01-03", "asset": "BTC", "close": 121.0},
        {"date": "2024-01-03", "asset": "ETH", "close": 15.0},
    ]
    pd.DataFrame(data).to_csv(csv_file, index=False)
    return csv_file


def test_integrity_check_valid_and_invalid(sample_csv: Path):
    """# FR-05, D-004: Checksum verification succeeds on match and fails with Portuguese error."""
    actual_hash = compute_file_sha256(sample_csv)
    assert len(actual_hash) == 64

    # Valid check
    verify_data_integrity(sample_csv, actual_hash)

    # Invalid check
    wrong_hash = "0" * 64
    with pytest.raises(ValueError, match="Erro de integridade dos dados"):
        verify_data_integrity(sample_csv, wrong_hash)


def test_load_and_validate_rules(sample_csv: Path, tmp_path: Path):
    """# NFR-04: Test enforcement of data model validation rules."""
    df = load_and_validate_prices(sample_csv)
    assert len(df) == 6
    assert list(df.columns) == ["date", "asset", "close"]

    # Rule: Missing columns
    bad_csv = tmp_path / "missing_col.csv"
    pd.DataFrame([{"date": "2024-01-01", "asset": "BTC"}]).to_csv(bad_csv, index=False)
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        load_and_validate_prices(bad_csv)

    # Rule: Close <= 0
    bad_price_csv = tmp_path / "bad_price.csv"
    pd.DataFrame([{"date": "2024-01-01", "asset": "BTC", "close": -5.0}]).to_csv(bad_price_csv, index=False)
    with pytest.raises(ValueError, match="menor ou igual a zero"):
        load_and_validate_prices(bad_price_csv)

    # Rule: Duplicate date-asset
    dup_csv = tmp_path / "dup.csv"
    pd.DataFrame([
        {"date": "2024-01-01", "asset": "BTC", "close": 100.0},
        {"date": "2024-01-01", "asset": "BTC", "close": 105.0},
    ]).to_csv(dup_csv, index=False)
    with pytest.raises(ValueError, match="registros duplicados"):
        load_and_validate_prices(dup_csv)


def test_hand_computed_returns_and_covariance(sample_csv: Path):
    """# FR-01: Verify return and covariance computation against manual calculation."""
    # Data:
    # Day 1: BTC=100, ETH=10
    # Day 2: BTC=110 (+10%), ETH=12 (+20%)
    # Day 3: BTC=121 (+10%), ETH=15 (+25%)
    # Returns BTC: [0.10, 0.10], Mean = 0.10, Var = 0.0
    # Returns ETH: [0.20, 0.25], Mean = 0.225, Var = 0.00125
    df = load_and_validate_prices(sample_csv)
    ret_matrix, mu, cov = compute_returns_and_scenarios(df)

    assert ret_matrix.shape == (2, 2)
    assert np.isclose(mu["BTC"], 0.10)
    assert np.isclose(mu["ETH"], 0.225)
    assert np.isclose(cov.loc["BTC", "BTC"], 0.0)
    assert np.isclose(cov.loc["ETH", "ETH"], 0.00125)
