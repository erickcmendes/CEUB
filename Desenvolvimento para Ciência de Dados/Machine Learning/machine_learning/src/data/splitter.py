"""
Estratégias de split treino/teste.

- Tabular: split aleatório com estratificação (classificação) ou sem (regressão)
- Séries temporais: split cronológico (sem embaralhamento)
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.utils.config import RANDOM_SEED, TEST_SIZE
from src.utils.logger import get_logger

logger = get_logger(__name__)


def tabular_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = TEST_SIZE,
    stratify: bool = True,
    random_state: int = RANDOM_SEED,
) -> tuple:
    """
    Split aleatório treino/teste para dados tabulares.

    Args:
        X: features
        y: target
        test_size: proporção do teste (default 0.20)
        stratify: se True, estratifica por y (apropriado para classificação)
    """
    stratify_arg = y if stratify else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_arg,
    )
    logger.info(f"Split tabular | treino: {X_train.shape} | teste: {X_test.shape}")
    return X_train, X_test, y_train, y_test


def temporal_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = TEST_SIZE,
) -> tuple:
    """
    Split cronológico para séries temporais — primeiros N% para treino,
    últimos (1-N)% para teste. NÃO embaralha.

    Args:
        X: features (geralmente sequências da janela rolante)
        y: target
        test_size: proporção do teste
    """
    n = len(X)
    cut = int(n * (1 - test_size))
    X_train, X_test = X[:cut], X[cut:]
    y_train, y_test = y[:cut], y[cut:]
    logger.info(f"Split temporal | treino: {X_train.shape} | teste: {X_test.shape}")
    return X_train, X_test, y_train, y_test
