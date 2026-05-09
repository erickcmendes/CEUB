"""
Pré-processamento de dados.

Inclui limpeza, conversão de tipos e tratamento de nulos.
"""
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def drop_nulls(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Remove linhas com valores nulos."""
    before = len(df)
    df = df.dropna(subset=subset).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        logger.info(f"Removidas {dropped} linhas com nulos")
    return df


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Garante que as colunas especificadas são numéricas."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def remove_outliers_iqr(df: pd.DataFrame, columns: list[str], k: float = 3.0) -> pd.DataFrame:
    """
    Remove outliers usando o método IQR (k=3.0 para outliers extremos).
    Conservador por padrão — não distorce a cauda em séries financeiras.
    """
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - k * iqr
        upper = q3 + k * iqr
        mask = (df[col] >= lower) & (df[col] <= upper)
        removed = (~mask).sum()
        if removed:
            logger.info(f"{col}: {removed} outliers removidos (IQR k={k})")
        df = df[mask]
    return df.reset_index(drop=True)


def add_returns_column(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    """Adiciona coluna de retorno percentual (variação diária)."""
    df = df.copy()
    df["retorno"] = df[price_col].pct_change()
    return df


def normalize_log(series: pd.Series) -> pd.Series:
    """Aplica log-transform para estabilizar variância em séries de preço."""
    return np.log(series.replace(0, np.nan)).dropna()
