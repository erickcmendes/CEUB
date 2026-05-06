"""
Engenharia de features para o dataset de carteiras simuladas.

A target principal é binária (sharpe_label) e os features são os pesos dos ativos.
"""
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Colunas-padrão que identificam pesos no df de carteiras
WEIGHT_PATTERNS = ["comp", "peso", "weight"]


def detect_weight_columns(df: pd.DataFrame) -> list[str]:
    """Detecta as colunas que representam pesos de ativos na carteira."""
    cols = [
        c for c in df.columns
        if any(p in c.lower() for p in WEIGHT_PATTERNS)
    ]
    if not cols:
        raise ValueError(
            "Nenhuma coluna de peso encontrada. "
            f"Esperado padrões: {WEIGHT_PATTERNS}"
        )
    return cols


def build_classification_dataset(df: pd.DataFrame, target: str = "sharpe_label") -> tuple:
    """
    Constrói X, y para classificação binária (boa/ruim carteira).

    Returns:
        X (DataFrame de features) e y (Series de target binário 0/1)
    """
    if target not in df.columns:
        raise ValueError(f"Target '{target}' não encontrado em {list(df.columns)}")
    weight_cols = detect_weight_columns(df)
    X = df[weight_cols].copy()
    y = df[target].astype(int).copy()
    logger.info(f"Classificação | features: {weight_cols} | target: {target}")
    logger.info(f"Distribuição do target: {y.value_counts().to_dict()}")
    return X, y


def build_regression_dataset(df: pd.DataFrame, target: str = "Retornos") -> tuple:
    """
    Constrói X, y para regressão de retorno esperado da carteira.

    Returns:
        X (DataFrame de features) e y (Series de retorno contínuo)
    """
    if target not in df.columns:
        raise ValueError(f"Target '{target}' não encontrado em {list(df.columns)}")
    weight_cols = detect_weight_columns(df)
    X = df[weight_cols].copy()
    y = df[target].astype(float).copy()
    logger.info(f"Regressão | features: {weight_cols} | target: {target}")
    return X, y
