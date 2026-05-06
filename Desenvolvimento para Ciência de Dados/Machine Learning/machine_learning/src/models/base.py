"""
Classe base abstrata para os modelos do projeto.

Define a interface comum: fit, predict, evaluate, save, load.
Garante consistência entre os wrappers de classificação, regressão e LSTM.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseModel(ABC):
    """Interface comum para todos os modelos."""

    name: str = "base"

    def __init__(self, **kwargs):
        self.model: Any = None
        self.params: dict = kwargs
        self.is_fitted: bool = False

    @abstractmethod
    def build(self) -> None:
        """Instancia o modelo subjacente com os hiperparâmetros configurados."""
        ...

    @abstractmethod
    def fit(self, X, y, **kwargs) -> "BaseModel":
        """Treina o modelo."""
        ...

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        """Gera predições."""
        ...

    def evaluate(self, X, y) -> dict:
        """Avalia o modelo. Implementação default delega para módulos de evaluation."""
        raise NotImplementedError("Subclasses devem implementar evaluate ou usar evaluator externo.")

    @abstractmethod
    def save(self, name: str) -> None:
        """Persiste o modelo no disco."""
        ...

    @abstractmethod
    def load(self, name: str) -> "BaseModel":
        """Carrega o modelo do disco."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} fitted={self.is_fitted}>"
