"""
Pipeline de treinamento da LSTM (single-layer).

Treina um modelo por ticker, reporta RMSE e MAE em dólares.

Uso:
    python -m pipelines.train_lstm
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.loader import load_coin
from src.data.splitter import temporal_split
from src.evaluation.regression_metrics import (
    evaluate_regressor,
    print_regression_report,
)
from src.features.timeseries_features import (
    inverse_scale,
    prepare_lstm_data,
)
from src.models.lstm_model import LSTMModel
from src.utils.config import CONFIG_DIR, REPORTS_DIR
from src.utils.logger import get_logger
from src.utils.persistence import save_metadata

logger = get_logger(__name__, log_file="train_lstm.log")


def train_one_ticker(ticker: str, cfg: dict) -> dict:
    """Treina e avalia uma LSTM para um ticker. Retorna dict de métricas."""
    logger.info(f"━━━ LSTM — {ticker} ━━━")

    # 1. Carregar e preparar dados
    df = load_coin(ticker)
    prep = prepare_lstm_data(
        df,
        price_col=cfg["price_col"],
        look_back=cfg["look_back_window"],
    )
    X, y, scaler = prep["X"], prep["y"], prep["scaler"]

    # 2. Split temporal (sem embaralhamento)
    X_train, X_test, y_train, y_test = temporal_split(X, y, test_size=cfg["test_size"])

    # 3. Construir e treinar modelo
    lstm = LSTMModel(
        look_back        = cfg["look_back_window"],
        units            = cfg["units"],
        dropout          = cfg["dropout"],
        batch_size       = cfg["batch_size"],
        epochs           = cfg["epochs"],
        patience         = cfg["patience"],
        learning_rate    = cfg["learning_rate"],
        validation_split = cfg["validation_split"],
        ticker           = ticker,
    )
    lstm.fit(X_train, y_train)

    # 4. Predição e inversão de escala
    y_pred_scaled = lstm.predict(X_test)
    y_pred_dollars = inverse_scale(y_pred_scaled, scaler)
    y_true_dollars = inverse_scale(y_test, scaler)

    # 5. Avaliação em dólares (RMSE e MAE em USD)
    metrics = evaluate_regressor(y_true_dollars, y_pred_dollars, in_dollars=True)
    print_regression_report(metrics, model_name=f"LSTM — {ticker}")

    # 6. Salvar
    lstm.save()
    save_metadata({
        "model":   f"lstm_{ticker}",
        "ticker":  ticker,
        "metrics": metrics,
        "config": {
            "look_back_window": cfg["look_back_window"],
            "units":            cfg["units"],
            "batch_size":       cfg["batch_size"],
            "epochs_max":       cfg["epochs"],
            "epochs_run":       len(lstm.history.history["loss"]),
            "dropout":          cfg["dropout"],
            "learning_rate":    cfg["learning_rate"],
        },
    }, name=f"lstm_{ticker}")

    return {
        "ticker": ticker,
        **metrics,
        "n_test_samples": int(len(y_test)),
    }


def main():
    cfg_path = CONFIG_DIR / "lstm_config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    tickers = cfg["tickers"]
    logger.info(f"Tickers a treinar: {tickers}")

    all_results = []
    for ticker in tickers:
        try:
            result = train_one_ticker(ticker, cfg)
            all_results.append(result)
        except Exception as e:
            logger.error(f"Falha ao treinar {ticker}: {e}", exc_info=True)

    # Tabela comparativa
    if all_results:
        df_results = pd.DataFrame(all_results)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_csv = REPORTS_DIR / "comparacao_lstm.csv"
        df_results.to_csv(out_csv, index=False)
        logger.info(f"Comparação LSTM salva em {out_csv}")

        print("\n📊 Resultados LSTM por Ticker (em dólares):")
        print(df_results.to_string(index=False))

    logger.info("Pipeline LSTM concluído com sucesso ✅")


if __name__ == "__main__":
    main()
