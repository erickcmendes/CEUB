# Data layer

**Phase:** 2 · A1 core · **Situation:** not started

## What it does

`data.py`: load the price file, check the checksum and stop with a Portuguese message if it differs, compute returns, the covariance matrix and the scenario matrix. Tests cover the data rules.

## What it does not do

It does not download from Yahoo and it does not forecast anything.

## Done when

- [ ] A wrong checksum stops the run with the agreed message
- [ ] Returns and covariance match a hand-computed toy case
- [ ] The data rules of the data model are tested

## Comes from

FR-05, NFR-01, NFR-05, D-004. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `src/portfolio_opt/data.py` and `tests/test_data.py`. Implemented SHA-256 integrity verification with Portuguese diagnostic messages, validation of all data model rules, pivot-based returns scenario matrix, expected returns vector, and sample covariance matrix. Tests cover hand-calculated toy cases and validation error conditions.

## How to test

Run `python -m pytest tests/test_data.py`. All tests should pass, confirming integrity verification, data rule enforcement, and mathematical accuracy of returns and covariance.
