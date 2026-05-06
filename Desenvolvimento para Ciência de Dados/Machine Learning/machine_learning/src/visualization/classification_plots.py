"""
Gráficos para análise de modelos de classificação.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import RocCurveDisplay

from src.utils.config import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str] = None,
    title: str = "Matriz de Confusão",
    save_as: str | None = None,
) -> Path | None:
    """Plota uma matriz de confusão com seaborn heatmap."""
    class_names = class_names or ["Ruim (0)", "Boa (1)"]
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True, fmt="d", cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=False, ax=ax,
        annot_kws={"size": 14},
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved


def plot_roc_curves(
    models: dict,
    X_test,
    y_test,
    title: str = "Curvas ROC",
    save_as: str | None = None,
) -> Path | None:
    """
    Plota as curvas ROC de múltiplos modelos no mesmo eixo.

    Args:
        models: dict {nome: modelo_com_predict_proba}
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, model in models.items():
        try:
            RocCurveDisplay.from_estimator(model, X_test, y_test, ax=ax, name=name)
        except Exception as e:
            logger.warning(f"Não foi possível plotar ROC de {name}: {e}")

    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", alpha=0.6, label="Aleatório")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved


def plot_metrics_comparison(
    df_compare,
    metrics: list[str] = None,
    save_as: str | None = None,
) -> Path | None:
    """Barras comparativas das métricas entre modelos."""
    metrics = metrics or ["accuracy", "precision", "recall", "f1"]
    df_plot = df_compare.set_index("modelo")[metrics]

    fig, ax = plt.subplots(figsize=(11, 6))
    df_plot.plot.bar(ax=ax, edgecolor="white")
    ax.set_title("Comparação de Métricas — Classificadores", fontsize=13, fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_xlabel("")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved
