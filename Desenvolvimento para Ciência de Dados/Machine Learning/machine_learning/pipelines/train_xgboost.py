"""
Pipeline de treinamento e fine-tuning do XGBoost.

Executa GridSearchCV em duas tarefas:
- Classificação (sharpe_label)
- Regressão (Retornos)

Uso:
    python -m pipelines.train_xgboost
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.loader import load_carteiras_ml
from src.data.splitter import tabular_split
from src.evaluation.classification_metrics import (
    evaluate_classifier,
    print_classification_report,
)
from src.evaluation.regression_metrics import (
    evaluate_regressor,
    print_regression_report,
)
from src.features.portfolio_features import (
    build_classification_dataset,
    build_regression_dataset,
)
from src.models.xgboost_model import XGBoostModel
from src.utils.config import CONFIG_DIR
from src.utils.logger import get_logger
from src.utils.persistence import save_metadata

logger = get_logger(__name__, log_file="train_xgboost.log")


def run_classification(cfg: dict, param_grid: dict, n_jobs: int):
    logger.info("━━━ XGBoost — Classificação ━━━")
    df = load_carteiras_ml()
    X, y = build_classification_dataset(df, target=cfg["target"])

    X_train, X_test, y_train, y_test = tabular_split(
        X, y,
        test_size=cfg["test_size"],
        stratify=True,
    )

    xgb = XGBoostModel(
        task="classification",
        param_grid=param_grid,
        cv_folds=cfg["cv_folds"],
        scoring=cfg["scoring"],
        n_jobs=n_jobs,
    )
    xgb.fit(X_train, y_train)

    y_pred = xgb.predict(X_test)
    y_proba = xgb.predict_proba(X_test)
    metrics = evaluate_classifier(y_test, y_pred, y_proba=y_proba)
    print_classification_report(metrics, model_name="XGBoost (Classificação)")

    xgb.save()
    save_metadata({
        "model": "xgboost_clf",
        "best_params": xgb.best_params_,
        "best_score_cv": xgb.best_score_,
        "metrics": {k: v for k, v in metrics.items() if k != "report_text"},
    }, name="xgboost_clf")


def run_regression(cfg: dict, param_grid: dict, n_jobs: int):
    logger.info("━━━ XGBoost — Regressão ━━━")
    df = load_carteiras_ml()
    X, y = build_regression_dataset(df, target=cfg["target"])

    X_train, X_test, y_train, y_test = tabular_split(
        X, y,
        test_size=cfg["test_size"],
        stratify=False,
    )

    xgb = XGBoostModel(
        task="regression",
        param_grid=param_grid,
        cv_folds=cfg["cv_folds"],
        scoring=cfg["scoring"],
        n_jobs=n_jobs,
    )
    xgb.fit(X_train, y_train)

    y_pred = xgb.predict(X_test)
    metrics = evaluate_regressor(y_test, y_pred, in_dollars=False)
    print_regression_report(metrics, model_name="XGBoost (Regressão)")

    xgb.save()
    save_metadata({
        "model": "xgboost_reg",
        "best_params": xgb.best_params_,
        "best_score_cv": xgb.best_score_,
        "metrics": metrics,
    }, name="xgboost_reg")


def main():
    cfg_path = CONFIG_DIR / "xgboost_config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    param_grid = cfg["param_grid"]
    n_jobs     = cfg.get("n_jobs", -1)

    run_classification(cfg["tasks"]["classification"], param_grid, n_jobs)
    run_regression    (cfg["tasks"]["regression"],     param_grid, n_jobs)

    logger.info("Pipeline XGBoost concluído com sucesso ✅")


if __name__ == "__main__":
    main()
