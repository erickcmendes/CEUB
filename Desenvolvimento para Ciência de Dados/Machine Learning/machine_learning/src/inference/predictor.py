"""
Wrapper de inferência: carrega modelos treinados e gera predições.

Usado pelo notebook de "insights melhorados por IA" e em scripts batch.
"""
from typing import Literal

import numpy as np
import pandas as pd

from src.features.timeseries_features import (
    inverse_scale,
    prepare_lstm_data,
)
from src.models.classifiers import get_classifier
from src.models.lstm_model import LSTMModel
from src.models.regressors import LinearRegressor
from src.models.xgboost_model import XGBoostModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioPredictor:
    """
    Predictor de carteiras (classificação + regressão).
    Carrega modelos previamente treinados.
    """
    def __init__(self, classifier_name: str = "random_forest"):
        self.classifier = get_classifier(classifier_name).load()
        self.regressor  = LinearRegressor().load()
        self.xgb_clf    = XGBoostModel(task="classification").load()
        self.xgb_reg    = XGBoostModel(task="regression").load()

    def predict_quality(self, weights: np.ndarray, use_xgb: bool = True) -> dict:
        """Prediz se a carteira é boa (1) ou ruim (0)."""
        weights = np.atleast_2d(weights)
        model = self.xgb_clf if use_xgb else self.classifier
        pred = int(model.predict(weights)[0])
        proba = float(model.predict_proba(weights)[0, 1])
        return {"sharpe_label_pred": pred, "prob_boa": proba}

    def predict_return(self, weights: np.ndarray, use_xgb: bool = True) -> float:
        """Prediz o retorno esperado da carteira."""
        weights = np.atleast_2d(weights)
        model = self.xgb_reg if use_xgb else self.regressor
        return float(model.predict(weights)[0])


class PricePredictor:
    """
    Predictor de preços via LSTM.
    Carrega o modelo de um ticker específico.
    """
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.lstm = LSTMModel(ticker=self.ticker).load()

    def predict_next_day(self, df_history: pd.DataFrame, price_col: str = "Close") -> float:
        """
        Prediz o preço do próximo dia a partir do histórico recente.

        Args:
            df_history: DataFrame com pelo menos `look_back` linhas
            price_col: nome da coluna de preço

        Returns:
            Preço previsto em dólares.
        """
        prep = prepare_lstm_data(df_history.tail(self.lstm.look_back + 1), price_col=price_col)
        # Pega apenas a última janela
        X_last = prep["X"][-1:]
        pred_scaled = self.lstm.predict(X_last)
        pred_dollars = inverse_scale(pred_scaled, prep["scaler"])
        return float(pred_dollars[0])

    def predict_horizon(
        self,
        df_history: pd.DataFrame,
        horizon: int = 7,
        price_col: str = "Close",
    ) -> np.ndarray:
        """
        Predição multi-step recursiva: usa cada predição como input do próximo passo.

        Args:
            horizon: número de dias à frente
        """
        prep = prepare_lstm_data(df_history, price_col=price_col)
        scaler = prep["scaler"]
        window = prep["X"][-1].flatten().tolist()  # último estado conhecido (escalonado)

        preds_scaled = []
        for _ in range(horizon):
            X_in = np.array(window[-self.lstm.look_back:]).reshape(1, self.lstm.look_back, 1)
            yhat = self.lstm.predict(X_in)[0]
            preds_scaled.append(yhat)
            window.append(yhat)

        return inverse_scale(np.array(preds_scaled), scaler)
