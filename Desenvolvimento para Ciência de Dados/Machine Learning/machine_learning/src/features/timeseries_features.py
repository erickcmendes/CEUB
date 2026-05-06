"""
Engenharia de features para séries temporais.

Inclui criação de janelas rolantes (sliding windows) e escalonamento
para entrada em redes neurais recorrentes.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.utils.config import LOOK_BACK_WINDOW
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_sequences(
    series: np.ndarray,
    look_back: int = LOOK_BACK_WINDOW,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Transforma uma série 1D em sequências (X, y) para LSTM.

    Cada exemplo X é uma janela de `look_back` valores consecutivos;
    o y correspondente é o próximo valor após a janela.

    Args:
        series: array 1D já escalonado
        look_back: tamanho da janela (default 90)

    Returns:
        X de shape (n_samples, look_back, 1)
        y de shape (n_samples,)
    """
    if len(series) <= look_back:
        raise ValueError(
            f"Série tem {len(series)} pontos, menor que look_back={look_back}"
        )
    X, y = [], []
    for i in range(look_back, len(series)):
        X.append(series[i - look_back:i])
        y.append(series[i])
    X = np.array(X).reshape(-1, look_back, 1)
    y = np.array(y)
    logger.info(f"Sequências criadas | X: {X.shape} | y: {y.shape}")
    return X, y


def scale_series(
    series: pd.Series,
    feature_range: tuple = (0, 1),
) -> tuple[np.ndarray, MinMaxScaler]:
    """
    Aplica MinMaxScaler em uma série de preços.

    Returns:
        Array escalonado (1D) e o scaler ajustado (necessário para inverter depois)
    """
    scaler = MinMaxScaler(feature_range=feature_range)
    values = series.values.reshape(-1, 1)
    scaled = scaler.fit_transform(values).flatten()
    return scaled, scaler


def inverse_scale(
    values: np.ndarray,
    scaler: MinMaxScaler,
) -> np.ndarray:
    """Inverte o escalonamento, devolvendo os valores em sua escala original."""
    return scaler.inverse_transform(values.reshape(-1, 1)).flatten()


def prepare_lstm_data(
    df: pd.DataFrame,
    price_col: str = "Close",
    look_back: int = LOOK_BACK_WINDOW,
) -> dict:
    """
    Pipeline completo de preparação de dados para LSTM:
    extrai a série de preço, escalona e cria sequências.

    Returns:
        Dict com 'X', 'y', 'scaler' e 'series_original' para inversão posterior.
    """
    if price_col not in df.columns:
        raise ValueError(f"Coluna {price_col!r} não encontrada em {list(df.columns)}")
    series = df[price_col].astype(float)
    scaled, scaler = scale_series(series)
    X, y = create_sequences(scaled, look_back=look_back)
    return {
        "X": X,
        "y": y,
        "scaler": scaler,
        "series_original": series.values,
    }
