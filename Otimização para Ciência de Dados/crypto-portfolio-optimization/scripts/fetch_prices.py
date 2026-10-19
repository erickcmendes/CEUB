"""
# NFR-04, NFR-05, D-002, D-004, T-001, T-004
Script to download historical daily crypto prices from Yahoo Finance,
clean and validate the data against data-model rules, save as CSV,
and print its SHA-256 checksum.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import pandas as pd
import yfinance as yf

# Default asset universe: liquid crypto assets
DEFAULT_TICKERS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
    "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD", "DOT-USD",
    "NEAR-USD", "LTC-USD", "UNI-USD", "ATOM-USD", "XLM-USD",
    "ETC-USD", "FIL-USD", "ICP-USD", "ALGO-USD", "BCH-USD"
]

DEFAULT_START = "2021-01-01"
DEFAULT_END = "2024-12-31"


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hexadecimal hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def fetch_crypto_prices(
    tickers: list[str],
    start_date: str,
    end_date: str,
    output_path: Path
) -> str:
    """# FR-05, NFR-05: Fetch, clean, and write crypto prices.

    Format required:
      - date: YYYY-MM-DD
      - asset: ticker symbol (e.g. BTC)
      - close: float > 0
    Sorted by date and asset, no duplicates, no missing dates.
    """
    print(f"Baixando dados para {len(tickers)} ativos de {start_date} até {end_date}...")
    
    # Download batch from yfinance
    df_raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if df_raw.empty:
        raise RuntimeError("Nenhum dado retornado do Yahoo Finance. Verifique a conexão.")

    # yfinance multi-ticker returns MultiIndex columns: ('Close', 'BTC-USD'), etc.
    if isinstance(df_raw.columns, pd.MultiIndex):
        if "Close" in df_raw.columns.levels[0]:
            df_close = df_raw["Close"]
        else:
            raise KeyError("Coluna 'Close' não encontrada no retorno do yfinance.")
    else:
        df_close = df_raw[["Close"]]

    # Forward fill then backward fill any isolated holidays/gaps across assets
    df_close = df_close.ffill().bfill()

    # Drop any remaining NaN columns if an asset didn't exist for the full period
    valid_cols = df_close.dropna(axis=1).columns.tolist()
    print(f"Ativos válidos com histórico contínuo: {len(valid_cols)} de {len(tickers)}")
    df_close = df_close[valid_cols]

    # Convert to tidy/long format (date, asset, close)
    records = []
    for dt, row in df_close.iterrows():
        dt_str = pd.Timestamp(dt).strftime("%Y-%m-%d")
        for ticker in valid_cols:
            asset_symbol = ticker.replace("-USD", "")
            close_val = float(row[ticker])
            if close_val <= 0:
                continue
            records.append({
                "date": dt_str,
                "asset": asset_symbol,
                "close": round(close_val, 6)
            })

    df_out = pd.DataFrame(records)
    
    # Sort by date and asset
    df_out.sort_values(by=["date", "asset"], inplace=True)
    df_out.drop_duplicates(subset=["date", "asset"], inplace=True)
    
    # Ensure parent dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with deterministic line endings
    df_out.to_csv(output_path, index=False, lineterminator="\n")
    
    sha256 = compute_sha256(output_path)
    print(f"Arquivo salvo em: {output_path}")
    print(f"Total de registros: {len(df_out)}")
    print(f"Ativos incluídos: {sorted(df_out['asset'].unique())}")
    print(f"SHA-256 Checksum: {sha256}")
    
    return sha256


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download daily crypto prices and compute checksum.")
    parser.add_argument("--output", type=str, default="data/crypto_prices.csv", help="Output path")
    parser.add_argument("--start", type=str, default=DEFAULT_START, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=DEFAULT_END, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    out_file = Path(args.output).resolve()
    fetch_crypto_prices(DEFAULT_TICKERS, args.start, args.end, out_file)
