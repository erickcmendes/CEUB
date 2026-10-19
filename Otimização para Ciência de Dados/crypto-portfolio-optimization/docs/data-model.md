# Data model

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-16

> **In short:** The project stores one input file of daily crypto prices, kept in Google Drive and not in GitHub. Everything else (returns, covariance, solutions, results) is computed on each run and lives in the notebook outputs. The rule that must not break: the notebook checks the file against a checksum before using it.

## What is stored

| What | What it holds | How many, roughly |
|---|---|---|
| Price file | Daily closing price of each candidate crypto asset, in US dollars | One file. Tens of assets and a few years of daily rows (deduced; the real size depends on D-002) |
| Checksum | The fingerprint of the price file, written inside the notebook | One value |

## How they relate

```
Price file --(checked by)--> Checksum
Price file --(computed on each run)--> returns, covariance, solutions, results
```

## Price file

Source: Yahoo Finance, extracted once with yfinance (D-002). Deduced format, to be confirmed after the first extraction.

| Field | What it is | Required | Rule |
|---|---|---|---|
| `date` | The calendar day of the price | yes | One row per asset per day, sorted |
| `asset` | The asset ticker, such as BTC | yes | Unique together with `date` |
| `close` | Closing price in US dollars | yes | Greater than zero, with no gap inside the window used |

**Personal data:** none.

## Rules that hold across them

- The file's checksum must match the one in the notebook, or the run stops with a clear message.
- The same window and the same assets are used by the exact model and by the genetic algorithm, so their results can be compared.
- The file is never committed to GitHub.

## What is not stored

- Returns, covariance and solutions: they are recomputed on each run, which keeps one source of truth.
- Personal data and company data: none is used (D-001).
- Intraday prices and trades: not needed for the course problem.
