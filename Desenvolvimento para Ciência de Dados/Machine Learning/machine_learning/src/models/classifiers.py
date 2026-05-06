"""
Modelos de classificação binária para o problema "carteira boa vs ruim".

Implementa wrappers padronizados para:
- KNN (K-Nearest Neighbors)
- Decision Tree
- Random Forest
- Logistic Regression

Hiperparâmetros padrão para baseline (fine-tuning é feito com XGBoost separadamente).
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from src.models.base import BaseModel
from src.utils.config import RANDOM_SEED
from src.utils.persistence import (
    load_sklearn_model,
    save_sklearn_model,
)


class SklearnClassifierWrapper(BaseModel):
    """Wrapper genérico para classificadores sklearn."""

    estimator_cls = None  # sobrescrito pelas subclasses

    def build(self) -> None:
        self.model = self.estimator_cls(**self.params)

    def fit(self, X, y, **kwargs) -> "SklearnClassifierWrapper":
        if self.model is None:
            self.build()
        self.model.fit(X, y, **kwargs)
        self.is_fitted = True
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        return self.model.predict_proba(X)

    def save(self, name: str | None = None) -> None:
        save_sklearn_model(self.model, name or self.name)

    def load(self, name: str | None = None) -> "SklearnClassifierWrapper":
        self.model = load_sklearn_model(name or self.name)
        self.is_fitted = True
        return self


class KNNClassifier(SklearnClassifierWrapper):
    """
    K-Nearest Neighbors.
    Baseline por similaridade — útil para mapear quais composições
    de carteira se agrupam em torno das "boas".
    """
    name = "knn_classifier"
    estimator_cls = KNeighborsClassifier

    def __init__(self, n_neighbors: int = 5, weights: str = "uniform", **kwargs):
        super().__init__(n_neighbors=n_neighbors, weights=weights, **kwargs)


class DecisionTreeClf(SklearnClassifierWrapper):
    """
    Árvore de Decisão.
    Modelo interpretável — gera regras de composição que separam boas e ruins.
    """
    name = "decision_tree_classifier"
    estimator_cls = DecisionTreeClassifier

    def __init__(self, max_depth: int | None = 6, criterion: str = "gini", **kwargs):
        super().__init__(
            max_depth=max_depth,
            criterion=criterion,
            random_state=RANDOM_SEED,
            **kwargs,
        )


class RandomForestClf(SklearnClassifierWrapper):
    """
    Random Forest.
    Reduz variância da árvore única e fornece feature importance robusta.
    """
    name = "random_forest_classifier"
    estimator_cls = RandomForestClassifier

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int | None = 10,
        n_jobs: int = -1,
        **kwargs,
    ):
        super().__init__(
            n_estimators=n_estimators,
            max_depth=max_depth,
            n_jobs=n_jobs,
            random_state=RANDOM_SEED,
            **kwargs,
        )


class LogisticRegressionClf(SklearnClassifierWrapper):
    """
    Regressão Logística.
    Fronteira linear entre carteiras boas e ruins; coeficientes
    indicam o peso relativo de cada ativo na classificação.
    """
    name = "logistic_regression"
    estimator_cls = LogisticRegression

    def __init__(self, C: float = 1.0, max_iter: int = 1000, **kwargs):
        super().__init__(
            C=C,
            max_iter=max_iter,
            random_state=RANDOM_SEED,
            **kwargs,
        )


# ── Registry ──────────────────────────────────────────────────────────────────
CLASSIFIER_REGISTRY = {
    "knn":                  KNNClassifier,
    "decision_tree":        DecisionTreeClf,
    "random_forest":        RandomForestClf,
    "logistic_regression":  LogisticRegressionClf,
}


def get_classifier(name: str, **kwargs) -> SklearnClassifierWrapper:
    """Factory function para instanciar um classificador pelo nome."""
    if name not in CLASSIFIER_REGISTRY:
        raise ValueError(
            f"Classificador desconhecido: {name}. "
            f"Disponíveis: {list(CLASSIFIER_REGISTRY)}"
        )
    return CLASSIFIER_REGISTRY[name](**kwargs)
