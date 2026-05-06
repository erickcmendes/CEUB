"""
Gráficos específicos para análise de modelos LSTM.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.utils.config import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def plot_training_history(
    history,
    title: str = "Curvas de Treinamento — LSTM",
    save_as: str | None = None,
) -> Path | None:
    """Plota loss e MAE por época (treino vs validação)."""
    h = history.history if hasattr(history, "history") else history

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Loss (MSE)
    axes[0].plot(h["loss"], label="Treino", color="#1976D2")
    if "val_loss" in h:
        axes[0].plot(h["val_loss"], label="Validação", color="#E64A19")
    axes[0].set_title("Loss (MSE)")
    axes[0].set_xlabel("Época")
    axes[0].set_ylabel("MSE")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # MAE
    if "mae" in h:
        axes[1].plot(h["mae"], label="Treino", color="#1976D2")
        if "val_mae" in h:
            axes[1].plot(h["val_mae"], label="Validação", color="#E64A19")
        axes[1].set_title("MAE")
        axes[1].set_xlabel("Época")
        axes[1].set_ylabel("MAE")
        axes[1].legend()
        axes[1].grid(alpha=0.3)

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


def plot_predictions_timeseries(
    y_true_dollars: np.ndarray,
    y_pred_dollars: np.ndarray,
    ticker: str,
    dates: np.ndarray | None = None,
    save_as: str | None = None,
) -> Path | None:
    """
    Plota a série de predições vs valores reais (em dólares) ao longo do tempo.
    """
    fig, ax = plt.subplots(figsize=(15, 6))

    x = dates if dates is not None else np.arange(len(y_true_dollars))

    ax.plot(x, y_true_dollars, label="Real",    color="#1976D2", linewidth=1.5)
    ax.plot(x, y_pred_dollars, label="Predito", color="#E64A19", linewidth=1.5, alpha=0.85)
    ax.fill_between(x, y_true_dollars, y_pred_dollars,
                    color="gray", alpha=0.15, label="Erro")

    ax.set_title(f"Predição LSTM — {ticker} (USD)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Data" if dates is not None else "Índice no conjunto de teste")
    ax.set_ylabel("Preço (USD)")
    ax.legend(loc="upper left")
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


def plot_error_distribution(
    y_true_dollars: np.ndarray,
    y_pred_dollars: np.ndarray,
    ticker: str,
    save_as: str | None = None,
) -> Path | None:
    """Distribuição do erro absoluto em dólares."""
    erros = y_true_dollars - y_pred_dollars
    erros_abs = np.abs(erros)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(erros, bins=40, color="#1976D2", alpha=0.75, edgecolor="white")
    axes[0].axvline(0, color="black", linestyle="--", linewidth=1)
    axes[0].set_title(f"Distribuição do Erro — {ticker}")
    axes[0].set_xlabel("Erro (USD)")
    axes[0].set_ylabel("Frequência")
    axes[0].grid(axis="y", alpha=0.3)

    axes[1].hist(erros_abs, bins=40, color="#E64A19", alpha=0.75, edgecolor="white")
    axes[1].axvline(erros_abs.mean(), color="black", linestyle="--",
                    linewidth=1, label=f"MAE = ${erros_abs.mean():,.2f}")
    axes[1].set_title(f"Distribuição do Erro Absoluto — {ticker}")
    axes[1].set_xlabel("|Erro| (USD)")
    axes[1].set_ylabel("Frequência")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    plt.tight_layout()

    saved = None
    if save_as:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        saved = FIGURES_DIR / save_as
        plt.savefig(saved, dpi=150, bbox_inches="tight")
        logger.info(f"Figura salva: {saved}")
    plt.show()
    return saved
