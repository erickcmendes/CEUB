"""
XGBoost com fine-tuning via GridSearchCV.

Diferente dos modelos baseline, o XGBoost é submetido a busca de hiperparâmetros
para servir como modelo de referência (state-of-the-art) na comparação.
"""
from typing import Literal

import numpy as np
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from xgboost import XGBClassifier, XGBRegressor

from src.models.base import BaseModel
from src.utils.config import RANDOM_SEED
from src.utils.logger import get_logger
from src.utils.persistence import (
    load_sklearn_model,
    save_sklearn_model,
)

logger = get_logger(__name__)


# Grid de busca padrão para fine-tuning
DEFAULT_PARAM_GRID = {
    "n_estimators":      [100, 300, 500],
    "max_depth":         [3, 5, 7],
    "learning_rate":     [0.01, 0.05, 0.1],
    "subsample":         [0.8, 1.0],
    "colsample_bytree":  [0.8, 1.0],
}


class XGBoostModel(BaseModel):
    """
    XGBoost com GridSearchCV.
    Suporta tanto classificação quanto regressão (parâmetro `task`).
    """
    name = "xgboost"

    def __init__(
        self,
        task: Literal["classification", "regression"] = "classification",
        param_grid: dict | None = None,
        cv_folds: int = 5,
        scoring: str | None = None,
        n_jobs: int = -1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.task = task
        self.param_grid = param_grid or DEFAULT_PARAM_GRID
        self.cv_folds = cv_folds
        self.scoring = scoring or ("f1" if task == "classification" else "r2")
        self.n_jobs = n_jobs
        self.search: GridSearchCV | None = None
        self.best_params_: dict | None = None
        self.best_score_: float | None = None

    def build(self) -> None:
        if self.task == "classification":
            base = XGBClassifier(
                random_state=RANDOM_SEED,
                eval_metric="logloss",
                n_jobs=self.n_jobs,
                **self.params,
            )
        else:
            base = XGBRegressor(
                random_state=RANDOM_SEED,
                n_jobs=self.n_jobs,
                **self.params,
            )
        self.model = base

    def fit(self, X, y, **kwargs) -> "XGBoostModel":
        if self.model is None:
            self.build()

        cv = (
            StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=RANDOM_SEED)
            if self.task == "classification"
            else self.cv_folds
        )

        logger.info(
            f"Iniciando GridSearchCV ({self.task}) | "
            f"folds={self.cv_folds} | scoring={self.scoring} | "
            f"combinações={self._n_combinations()}"
        )

        self.search = GridSearchCV(
            estimator=self.model,
            param_grid=self.param_grid,
            cv=cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            verbose=1,
            return_train_score=True,
        )
        self.search.fit(X, y, **kwargs)

        self.model = self.search.best_estimator_
        self.best_params_ = self.search.best_params_
        self.best_score_ = float(self.search.best_score_)
        self.is_fitted = True

        logger.info(f"Melhores parâmetros: {self.best_params_}")
        logger.info(f"Melhor score CV: {self.best_score_:.4f}")
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        if self.task != "classification":
            raise NotImplementedError("predict_proba só está disponível para classificação")
        return self.model.predict_proba(X)

    def _n_combinations(self) -> int:
        n = 1
        for v in self.param_grid.values():
            n *= len(v)
        return n

    def save(self, name: str | None = None) -> None:
        suffix = "clf" if self.task == "classification" else "reg"
        save_sklearn_model(self.model, name or f"{self.name}_{suffix}")

    def load(self, name: str | None = None) -> "XGBoostModel":
        suffix = "clf" if self.task == "classification" else "reg"
        self.model = load_sklearn_model(name or f"{self.name}_{suffix}")
        self.is_fitted = True
        return self
