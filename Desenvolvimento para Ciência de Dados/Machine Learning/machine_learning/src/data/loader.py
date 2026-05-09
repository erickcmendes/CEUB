"""
Carregamento de dados a partir dos arquivos CSV do projeto.
"""
from pathlib import Path

import pandas as pd

from src.utils.config import (
    CARTEIRAS_ML_CSV,
    COIN_CSVS,
    HISTORICO_CSV,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_carteiras_ml() -> pd.DataFrame:
    """Carrega o dataset de carteiras simuladas com sharpe_label."""
    if not CARTEIRAS_ML_CSV.exists():
        raise FileNotFoundError(
            f"{CARTEIRAS_ML_CSV} não encontrado. "
            "Execute o notebook eda_insights.ipynb antes."
        )
    df = pd.read_csv(CARTEIRAS_ML_CSV)
    logger.info(f"carteiras_ml carregado: {df.shape}")
    return df


def load_historico() -> pd.DataFrame:
    """Carrega o histórico unificado (formato long: moeda, date, retorno, preco)."""
    if not HISTORICO_CSV.exists():
        raise FileNotFoundError(
            f"{HISTORICO_CSV} não encontrado. "
            "Execute o notebook eda_inicial.ipynb antes."
        )
    df = pd.read_csv(HISTORICO_CSV, parse_dates=["date"])
    logger.info(f"historico carregado: {df.shape}")
    return df


def load_coin(ticker: str) -> pd.DataFrame:
    """Carrega o histórico individual de uma criptomoeda (BTC, ETH, XRP, DASH)."""
    ticker = ticker.upper()
    if ticker not in COIN_CSVS:
        raise ValueError(f"Ticker desconhecido: {ticker}. Disponíveis: {list(COIN_CSVS)}")
    path: Path = COIN_CSVS[ticker]
    if not path.exists():
        raise FileNotFoundError(
            f"{path} não encontrado. Execute o notebook ETL_moedas.ipynb antes."
        )
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"{ticker} carregado: {df.shape} (de {df['date'].min().date()} a {df['date'].max().date()})")
    return df


def load_all_coins() -> dict[str, pd.DataFrame]:
    """Carrega todas as criptomoedas disponíveis."""
    return {ticker: load_coin(ticker) for ticker in COIN_CSVS}
