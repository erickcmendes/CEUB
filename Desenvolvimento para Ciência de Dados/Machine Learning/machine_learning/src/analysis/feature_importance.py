"""
Análise de importância de features.

Suporta:
- Modelos baseados em árvore (DT, RF, XGBoost): atributo .feature_importances_
- Modelos lineares (LogReg, LinearReg): atributo .coef_
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.config import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_feature_importance(model, feature_names: list[str]) -> pd.DataFrame:
    """
    Extrai importância de features de um modelo.

    Tenta `feature_importances_` (tree-based) e depois `coef_` (linear).

    Returns:
        DataFrame com colunas ['feature', 'importance'] ordenado.
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        kind = "tree-based"
    elif hasattr(model, "coef_"):
        coef = model.coef_
        importances = np.abs(coef.flatten() if coef.ndim > 1 else coef)
        kind = "linear (|coef|)"
    else:
        raise ValueError(
            f"Modelo {type(model).__name__} não expõe feature_importances_ nem coef_"
        )

    df = pd.DataFrame({
        "feature":    feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    logger.info(f"Feature importance ({kind}) calculada para {len(feature_names)} features")
    return df


def plot_feature_importance(
    df_importance: pd.DataFrame,
    title: str = "Importância de Features",
    save_as: str | None = None,
) -> Path | None:
    """Plota o ranking de importâncias em barras horizontais."""
    fig, ax = plt.subplots(figsize=(8, max(4, len(df_importance) * 0.4)))
    ax.barh(df_importance["feature"], df_importance["importance"],
            color="#1976D2", edgecolor="white")
    ax.invert_yaxis()
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Importância")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved
