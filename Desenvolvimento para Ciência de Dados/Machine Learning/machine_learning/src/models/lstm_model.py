"""
LSTM (Long Short-Term Memory) para previsão de séries temporais de preços.

Arquitetura: LSTM não-empilhada (single layer) seguida de Dense(1).
- units=100 (configurável)
- look_back_window=90 dias na entrada
- Loss: MSE
- Otimizador: Adam
- Métricas reportadas em dólares: RMSE, MAE
- EarlyStopping para evitar overfitting
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from src.models.base import BaseModel
from src.utils.config import (
    LSTM_BATCH_SIZE,
    LSTM_MAX_EPOCHS,
    LSTM_PATIENCE,
    LSTM_UNITS,
    LOOK_BACK_WINDOW,
    RANDOM_SEED,
)
from src.utils.logger import get_logger
from src.utils.persistence import (
    load_keras_model,
    save_keras_model,
)

logger = get_logger(__name__)


class LSTMModel(BaseModel):
    """
    LSTM single-layer para previsão de preço de criptomoeda.

    Por enunciado:
    - units = 100
    - look_back_window = 90
    - batch_size = 32
    - epochs <= 200
    - EarlyStopping
    - Loss = MSE
    """
    name = "lstm"

    def __init__(
        self,
        look_back: int = LOOK_BACK_WINDOW,
        units: int = LSTM_UNITS,
        dropout: float = 0.2,
        batch_size: int = LSTM_BATCH_SIZE,
        epochs: int = LSTM_MAX_EPOCHS,
        patience: int = LSTM_PATIENCE,
        learning_rate: float = 0.001,
        validation_split: float = 0.1,
        ticker: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.look_back        = look_back
        self.units            = units
        self.dropout          = dropout
        self.batch_size       = batch_size
        self.epochs           = epochs
        self.patience         = patience
        self.learning_rate    = learning_rate
        self.validation_split = validation_split
        self.ticker           = ticker
        self.history          = None

    def build(self) -> None:
        # Imports atrasados para evitar custo de TF quando o módulo não é usado
        import tensorflow as tf
        from tensorflow.keras import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
        from tensorflow.keras.optimizers import Adam

        tf.random.set_seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

        model = Sequential([
            Input(shape=(self.look_back, 1)),
            LSTM(units=self.units, return_sequences=False),
            Dropout(self.dropout),
            Dense(1, activation="linear"),
        ])
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss="mse",
            metrics=["mae"],
        )
        self.model = model
        logger.info(f"LSTM construída | units={self.units} | look_back={self.look_back}")

    def fit(self, X, y, **kwargs) -> "LSTMModel":
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

        if self.model is None:
            self.build()

        callbacks = [
            EarlyStopping(
                monitor="val_loss",
                patience=self.patience,
                restore_best_weights=True,
                verbose=1,
            ),
            ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=max(self.patience // 2, 3),
                min_lr=1e-6,
                verbose=1,
            ),
        ]

        logger.info(
            f"Treinando LSTM | epochs<= {self.epochs} | batch_size={self.batch_size} | "
            f"validation_split={self.validation_split}"
        )

        self.history = self.model.fit(
            X, y,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=self.validation_split,
            callbacks=callbacks,
            verbose=kwargs.pop("verbose", 1),
            shuffle=False,  # respeito à ordem temporal
            **kwargs,
        )
        self.is_fitted = True
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X, verbose=0).flatten()

    def save(self, name: str | None = None) -> None:
        suffix = f"_{self.ticker}" if self.ticker else ""
        save_keras_model(self.model, name or f"{self.name}{suffix}")

    def load(self, name: str | None = None) -> "LSTMModel":
        suffix = f"_{self.ticker}" if self.ticker else ""
        self.model = load_keras_model(name or f"{self.name}{suffix}")
        self.is_fitted = True
        return self
