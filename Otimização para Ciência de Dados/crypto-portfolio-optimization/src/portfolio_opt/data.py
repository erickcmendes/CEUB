"""
# FR-05, NFR-01, NFR-05, D-004
Data layer: Ingestion, SHA-256 integrity verification, validation, and financial moments computation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def compute_file_sha256(file_path: str | Path) -> str:
    """# NFR-05, D-004: Compute SHA-256 hexadecimal digest of a local file."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado no caminho especificado: {p}")
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_data_integrity(file_path: str | Path, expected_sha256: str) -> None:
    """# FR-05, D-004: Verify file integrity against expected SHA-256.

    Stops with an informative Portuguese message if mismatched.
    """
    actual_hash = compute_file_sha256(file_path)
    if actual_hash.lower() != expected_sha256.lower():
        raise ValueError(
            f"Erro de integridade dos dados: O hash SHA-256 do arquivo ({actual_hash}) "
            f"diverge do esperado ({expected_sha256}). O arquivo pode estar corrompido ou desatualizado."
        )


def load_and_validate_prices(
    file_path: str | Path,
    expected_sha256: str | None = None
) -> pd.DataFrame:
    """# FR-05, NFR-04: Load price dataset and validate against data-model rules.

    Rules:
    - Required columns: 'date', 'asset', 'close'
    - 'close' must be strictly positive
    - No duplicate (date, asset) entries
    - No null/NaN values
    """
    if expected_sha256 is not None:
        verify_data_integrity(file_path, expected_sha256)

    df = pd.read_csv(file_path)
    required_cols = {"date", "asset", "close"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes no arquivo de preços: {missing}")

    if df.empty:
        raise ValueError("O arquivo de preços está vazio.")

    # Rule: no nulls
    if df[list(required_cols)].isna().any().any():
        raise ValueError("O conjunto de dados contém valores nulos/ausentes.")

    # Rule: close > 0
    if (df["close"] <= 0).any():
        raise ValueError("O arquivo contém cotações com valor menor ou igual a zero.")

    # Rule: no duplicates
    if df.duplicated(subset=["date", "asset"]).any():
        raise ValueError("Existem registros duplicados para o mesmo par (data, ativo).")

    df["date"] = pd.to_datetime(df["date"])
    df["asset"] = df["asset"].astype(str)
    df["close"] = df["close"].astype(float)
    df.sort_values(by=["date", "asset"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def compute_returns_and_scenarios(
    df_prices: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """# FR-01, FR-02: Compute daily returns matrix, mean vector, and covariance matrix.

    Returns:
        returns_matrix (pd.DataFrame): Scenario matrix T x N of daily percentage returns.
        mean_returns (pd.Series): Expected return vector mu of length N.
        cov_matrix (pd.DataFrame): Covariance matrix Sigma of shape N x N.
    """
    # Pivot to wide format: index=date, columns=asset, values=close
    prices_wide = df_prices.pivot(index="date", columns="asset", values="close")
    
    # Compute daily percentage returns
    returns_matrix = prices_wide.pct_change().dropna()
    
    if returns_matrix.empty:
        raise ValueError("Não há dados suficientes para calcular os retornos diários.")

    mean_returns = returns_matrix.mean()
    cov_matrix = returns_matrix.cov()

    return returns_matrix, mean_returns, cov_matrix
