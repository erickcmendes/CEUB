"""
Métricas para problemas de regressão.

Inclui R², MAE, RMSE, MAPE — em escala original (dólares quando aplicável).
"""
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)


def evaluate_regressor(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    in_dollars: bool = False,
) -> dict:
    """
    Calcula as métricas de regressão.

    Args:
        y_true: valores reais
        y_pred: valores preditos
        in_dollars: se True, marca as métricas como sendo em escala monetária
                    (sem conversão — apenas anota no metadata)

    Returns:
        Dict com r2, mae, rmse, mape.
    """
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))

    try:
        mape = float(mean_absolute_percentage_error(y_true, y_pred))
    except Exception:
        mape = None

    metrics = {
        "r2":   r2,
        "mae":  mae,
        "rmse": rmse,
        "mape": mape,
        "unit": "USD" if in_dollars else "raw",
    }
    return metrics


def print_regression_report(metrics: dict, model_name: str = "") -> None:
    """Imprime as métricas de regressão de forma legível."""
    unit = metrics.get("unit", "raw")
    suffix = " USD" if unit == "USD" else ""
    print(f"\n{'═' * 60}")
    print(f"  {model_name}")
    print(f"{'═' * 60}")
    print(f"  R²   : {metrics['r2']:.4f}")
    print(f"  MAE  : {metrics['mae']:.4f}{suffix}")
    print(f"  RMSE : {metrics['rmse']:.4f}{suffix}")
    if metrics.get("mape") is not None:
        print(f"  MAPE : {metrics['mape'] * 100:.2f}%")
    print(f"{'═' * 60}\n")
