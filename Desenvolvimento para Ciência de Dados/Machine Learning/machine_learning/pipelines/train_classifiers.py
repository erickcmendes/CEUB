"""
Pipeline de treinamento dos classificadores baseline.

Executa: KNN, Decision Tree, Random Forest, Logistic Regression.
Salva modelos em outputs/models/ e relatório CSV em outputs/reports/.

Uso:
    python -m pipelines.train_classifiers
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.loader import load_carteiras_ml
from src.data.splitter import tabular_split
from src.evaluation.classification_metrics import (
    evaluate_classifier,
    print_classification_report,
)
from src.evaluation.model_comparator import compare_classifiers
from src.features.portfolio_features import build_classification_dataset
from src.models.classifiers import get_classifier
from src.utils.config import CONFIG_DIR
from src.utils.logger import get_logger
from src.utils.persistence import save_metadata

logger = get_logger(__name__, log_file="train_classifiers.log")


def main():
    # ── 1. Carregar config ──────────────────────────────────────────────────
    cfg_path = CONFIG_DIR / "classifiers_config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logger.info(f"Config carregado de {cfg_path}")

    # ── 2. Carregar dados ───────────────────────────────────────────────────
    df = load_carteiras_ml()
    X, y = build_classification_dataset(df, target=cfg["target"])

    # ── 3. Split ────────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = tabular_split(
        X, y,
        test_size=cfg["test_size"],
        stratify=cfg["stratify"],
    )

    # ── 4. Padronização (somente para KNN e LogReg) ─────────────────────────
    scaler = None
    if cfg.get("scale_features", True):
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled  = scaler.transform(X_test)
    else:
        X_train_scaled, X_test_scaled = X_train.values, X_test.values

    SCALE_SENSITIVE = {"knn", "logistic_regression"}

    # ── 5. Treinar e avaliar cada modelo ────────────────────────────────────
    results: dict[str, dict] = {}
    for model_name, params in cfg["models"].items():
        logger.info(f"━━━ Treinando: {model_name} ━━━")
        clf = get_classifier(model_name, **params)

        if model_name in SCALE_SENSITIVE:
            X_tr, X_te = X_train_scaled, X_test_scaled
        else:
            X_tr, X_te = X_train.values, X_test.values

        clf.fit(X_tr, y_train)

        y_pred = clf.predict(X_te)
        y_proba = clf.predict_proba(X_te) if hasattr(clf, "predict_proba") else None

        metrics = evaluate_classifier(y_test, y_pred, y_proba=y_proba)
        results[model_name] = metrics
        print_classification_report(metrics, model_name=model_name)

        # Salvar modelo
        clf.save()
        save_metadata({
            "model":  model_name,
            "params": params,
            "metrics": {k: v for k, v in metrics.items() if k != "report_text"},
        }, name=clf.name)

    # ── 6. Salvar comparação ────────────────────────────────────────────────
    df_compare = compare_classifiers(results)
    print("\n📊 Comparação Final dos Classificadores:")
    print(df_compare.to_string(index=False))

    logger.info("Pipeline de classificação concluído com sucesso ✅")


if __name__ == "__main__":
    main()
