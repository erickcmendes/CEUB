"""
Métricas para problemas de classificação.

Inclui: acurácia, precision, recall, F1, matriz de confusão, ROC-AUC.
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
    average: str = "binary",
) -> dict:
    """
    Calcula todas as métricas obrigatórias para classificação binária.

    Args:
        y_true: rótulos reais
        y_pred: rótulos preditos
        y_proba: probabilidades preditas (para ROC-AUC). Opcional.
        average: estratégia de agregação para multi-classe ('binary' por padrão)

    Returns:
        Dicionário com todas as métricas.
    """
    metrics = {
        "accuracy":          float(accuracy_score(y_true, y_pred)),
        "precision":         float(precision_score(y_true, y_pred, average=average, zero_division=0)),
        "recall":            float(recall_score(y_true, y_pred, average=average, zero_division=0)),
        "f1":                float(f1_score(y_true, y_pred, average=average, zero_division=0)),
        "confusion_matrix":  confusion_matrix(y_true, y_pred).tolist(),
    }

    if y_proba is not None:
        try:
            # binário: passar a probabilidade da classe positiva
            proba_pos = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
            metrics["roc_auc"] = float(roc_auc_score(y_true, proba_pos))
        except Exception:
            metrics["roc_auc"] = None

    metrics["report_text"] = classification_report(y_true, y_pred, zero_division=0)
    return metrics


def print_classification_report(metrics: dict, model_name: str = "") -> None:
    """Imprime as métricas de forma legível."""
    print(f"\n{'═' * 60}")
    print(f"  {model_name}")
    print(f"{'═' * 60}")
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall   : {metrics['recall']:.4f}")
    print(f"  F1-Score : {metrics['f1']:.4f}")
    if metrics.get("roc_auc") is not None:
        print(f"  ROC-AUC  : {metrics['roc_auc']:.4f}")
    print(f"  Confusion Matrix:")
    cm = metrics["confusion_matrix"]
    print(f"    [[TN={cm[0][0]:5d}  FP={cm[0][1]:5d}]")
    print(f"     [FN={cm[1][0]:5d}  TP={cm[1][1]:5d}]]")
    print(f"{'═' * 60}\n")
