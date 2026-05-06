"""
Modelos de regressão para previsão de retorno esperado da carteira.
"""
import numpy as np
from sklearn.linear_model import LinearRegression

from src.models.base import BaseModel
from src.utils.persistence import (
    load_sklearn_model,
    save_sklearn_model,
)


class LinearRegressor(BaseModel):
    """
    Regressão Linear.
    Ajusta um plano que relaciona os pesos dos ativos ao retorno esperado.
    Coeficientes têm interpretação direta como contribuição de cada ativo.
    """
    name = "linear_regression"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self) -> None:
        self.model = LinearRegression(**self.params)

    def fit(self, X, y, **kwargs) -> "LinearRegressor":
        if self.model is None:
            self.build()
        self.model.fit(X, y, **kwargs)
        self.is_fitted = True
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    @property
    def coefficients(self) -> np.ndarray:
        return self.model.coef_

    @property
    def intercept(self) -> float:
        return float(self.model.intercept_)

    def save(self, name: str | None = None) -> None:
        save_sklearn_model(self.model, name or self.name)

    def load(self, name: str | None = None) -> "LinearRegressor":
        self.model = load_sklearn_model(name or self.name)
        self.is_fitted = True
        return self
