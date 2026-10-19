# Extract the prices

**Phase:** 1 · Foundations · **Situation:** not started

## What it does

`scripts/fetch_prices.py`: it downloads daily closes with yfinance for the chosen assets and window, cleans them, writes the price file in the format of the data model, and prints its SHA-256 checksum. The student runs it once, uploads the file to Drive, and shares it by link.

## What it does not do

It does not run in the evaluator's notebook, and it does not commit the file to GitHub.

## Done when

- [ ] The file has date, asset and close, with no gaps in the window and no duplicate date and asset pair
- [ ] The checksum is printed and the same file gives the same checksum
- [ ] The Yahoo terms of use were read and the result is in the test plan (T-001)
- [ ] The extraction works from the student's environment (T-004)

## Comes from

NFR-04, NFR-05, D-002, D-004, T-001, T-004. Waits for the student to run it, upload the file and read the Yahoo terms. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `scripts/fetch_prices.py`. Extracted 27,740 records across 19 liquid cryptocurrencies between 2021-01-01 and 2024-12-31 without gaps or duplicates. Generated `data/crypto_prices.csv` with SHA-256 checksum:
`10d98d487cc565341296462c5cb29efa876e0dbf56cdcde46310aa73b21eaba8`.

## How to test

Run `python scripts/fetch_prices.py`. Check that `data/crypto_prices.csv` is generated with 27,740 rows and that calculating `hashlib.sha256` on the resulting file matches `10d98d487cc565341296462c5cb29efa876e0dbf56cdcde46310aa73b21eaba8`.
