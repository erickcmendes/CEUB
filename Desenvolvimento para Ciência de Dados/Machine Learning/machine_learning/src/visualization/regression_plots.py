"""
Gráficos para análise de modelos de regressão.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.utils.config import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def plot_predicted_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = "Predito vs Real",
    save_as: str | None = None,
) -> Path | None:
    """Scatter de y_pred vs y_true com a linha y=x como referência."""
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(y_true, y_pred, alpha=0.4, s=15, edgecolor="none", color="#1976D2")

    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, "k--", linewidth=1.2, label="y = x")

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Valor Real")
    ax.set_ylabel("Valor Predito")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_aspect("equal", adjustable="box")
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved


def plot_residuals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = "Análise de Resíduos",
    save_as: str | None = None,
) -> Path | None:
    """Scatter dos resíduos + histograma."""
    residuos = y_true - y_pred

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].scatter(y_pred, residuos, alpha=0.4, s=15, color="#E64A19")
    axes[0].axhline(0, color="black", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Valor Predito")
    axes[0].set_ylabel("Resíduo (real − predito)")
    axes[0].set_title("Resíduos vs Predito")
    axes[0].grid(alpha=0.3)

    axes[1].hist(residuos, bins=40, color="#E64A19", alpha=0.75, edgecolor="white")
    axes[1].axvline(0, color="black", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Resíduo")
    axes[1].set_ylabel("Frequência")
    axes[1].set_title("Distribuição dos Resíduos")
    axes[1].grid(axis="y", alpha=0.3)

    plt.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved
