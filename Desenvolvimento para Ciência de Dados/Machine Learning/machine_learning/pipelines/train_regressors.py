"""
Pipeline de treinamento da regressão baseline.

Executa: Regressão Linear sobre o retorno esperado da carteira.

Uso:
    python -m pipelines.train_regressors
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.loader import load_carteiras_ml
from src.data.splitter import tabular_split
from src.evaluation.regression_metrics import (
    evaluate_regressor,
    print_regression_report,
)
from src.evaluation.model_comparator import compare_regressors
from src.features.portfolio_features import build_regression_dataset
from src.models.regressors import LinearRegressor
from src.utils.config import CONFIG_DIR
from src.utils.logger import get_logger
from src.utils.persistence import save_metadata

logger = get_logger(__name__, log_file="train_regressors.log")


def main():
    # ── 1. Carregar config ──────────────────────────────────────────────────
    cfg_path = CONFIG_DIR / "regressors_config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # ── 2. Carregar dados ───────────────────────────────────────────────────
    df = load_carteiras_ml()
    X, y = build_regression_dataset(df, target=cfg["target"])

    # ── 3. Split ────────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = tabular_split(
        X, y,
        test_size=cfg["test_size"],
        stratify=False,
    )

    # ── 4. Treinar ──────────────────────────────────────────────────────────
    results: dict[str, dict] = {}
    for model_name, params in cfg["models"].items():
        logger.info(f"━━━ Treinando: {model_name} ━━━")
        reg = LinearRegressor(**params)
        reg.fit(X_train, y_train)

        y_pred = reg.predict(X_test)
        metrics = evaluate_regressor(y_test, y_pred, in_dollars=False)
        results[model_name] = metrics
        print_regression_report(metrics, model_name=model_name)

        reg.save()
        save_metadata({
            "model":  model_name,
            "params": params,
            "metrics": metrics,
            "coefficients": reg.coefficients.tolist(),
            "intercept":    reg.intercept,
            "feature_names": list(X.columns),
        }, name=reg.name)

    # ── 5. Salvar comparação ────────────────────────────────────────────────
    df_compare = compare_regressors(results)
    print("\n📊 Comparação Final dos Regressores:")
    print(df_compare.to_string(index=False))

    logger.info("Pipeline de regressão concluído com sucesso ✅")


if __name__ == "__main__":
    main()
