"""
Comparação de modelos.

Recebe os resultados de múltiplos modelos e gera um DataFrame comparativo
para a seção "Comparação de Modelos" do projeto.
"""
import pandas as pd

from src.utils.config import REPORTS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def compare_classifiers(results: dict[str, dict], save: bool = True) -> pd.DataFrame:
    """
    Args:
        results: dict no formato {model_name: metrics_dict}
        save: se True, salva CSV em outputs/reports/

    Returns:
        DataFrame ordenado por F1-score decrescente.
    """
    rows = []
    for name, m in results.items():
        rows.append({
            "modelo":    name,
            "accuracy":  m.get("accuracy"),
            "precision": m.get("precision"),
            "recall":    m.get("recall"),
            "f1":        m.get("f1"),
            "roc_auc":   m.get("roc_auc"),
        })
    df = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    if save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / "comparacao_classificadores.csv"
        df.to_csv(path, index=False)
        logger.info(f"Comparação salva em {path}")
    return df


def compare_regressors(results: dict[str, dict], save: bool = True) -> pd.DataFrame:
    """
    Args:
        results: dict no formato {model_name: metrics_dict}
        save: se True, salva CSV em outputs/reports/

    Returns:
        DataFrame ordenado por RMSE crescente.
    """
    rows = []
    for name, m in results.items():
        rows.append({
            "modelo": name,
            "r2":     m.get("r2"),
            "mae":    m.get("mae"),
            "rmse":   m.get("rmse"),
            "mape":   m.get("mape"),
            "unit":   m.get("unit", "raw"),
        })
    df = pd.DataFrame(rows).sort_values("rmse").reset_index(drop=True)
    if save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / "comparacao_regressores.csv"
        df.to_csv(path, index=False)
        logger.info(f"Comparação salva em {path}")
    return df
