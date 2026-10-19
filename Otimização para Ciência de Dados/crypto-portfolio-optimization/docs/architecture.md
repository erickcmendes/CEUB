# Architecture

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-17

> **In short:** One Python package with tests, living in the portfolio repository github.com/erickcmendes/CEUB, does all the work. A Portuguese Colab notebook installs that package at a pinned tag, downloads one fixed price file from Google Drive, and shows the results. Prices are extracted once from Yahoo Finance on the student's machine. Before changing the package, remember that the notebook depends on its tag.

## Overview

```
Student's machine                  Google Drive                    GitHub: erickcmendes/CEUB
scripts/fetch_prices.py  ------>  prices.csv (link sharing)        src/portfolio_opt  (tagged release)
   (yfinance, once)                      |                                 |
                                         | gdown + checksum                | pip install @ tag
                                         v                                 v
                             Colab runtime of the evaluator (free)
                             notebook (Portuguese): setup -> data -> formulation
                               -> exact models (CBC, Ipopt, Couenne) -> genetic algorithm -> gap report
```

All logic lives in the package. The notebook only orchestrates, explains in Portuguese, and prints the source of the main functions on screen, so the evaluator reads the real code and the two deliverables cannot drift apart.

## The parts

| Part | Where it runs | What it does |
|---|---|---|
| `scripts/fetch_prices.py` | The student's machine, once | Extracts daily closes with yfinance, writes the price file and its SHA-256 checksum |
| Price file | Google Drive, shared by link | The fixed snapshot of prices (D-004) |
| `portfolio_opt` package | Colab runtime, and the student's tests | Data loading, the three exact models, the genetic algorithm, metrics |
| Colab notebook (Portuguese) | The evaluator's free Colab runtime | Installs the solvers and the package, downloads and checks the file, runs everything, explains it |
| Tests (`pytest`) | The student's machine and Colab | Check the models on a toy instance with a known optimum, and the data rules |

## How the code is organised

```
<project folder in the CEUB repository>/
  README.md              English, for the portfolio
  pyproject.toml         package metadata and pinned dependencies
  src/portfolio_opt/
    params.py            the PARAMS cell: cardinality, bounds, risk level, seed, window
    data.py              load, checksum, returns, covariance, scenarios
    models.py            Pyomo models: CVaR MILP, mean-variance NLP, cardinality MINLP
    solvers.py           solver setup and a solve wrapper with status and timing
    ga.py                DEAP genetic algorithm
    metrics.py           return, risk, CVaR, gap to the exact optimum
  scripts/fetch_prices.py
  notebooks/a1_colab_pt.ipynb
  tests/
  docs/                  these documents
```

The rule: logic goes in `src/`, notebooks only call it. Every public function names the requirement or decision it serves (for example FR-02, D-006) in its docstring.

## Data

| What is stored | What it holds | Personal data |
|---|---|---|
| Price file (Drive) | Daily closing prices of the chosen assets, from Yahoo Finance | No |
| Checksum | The SHA-256 of the price file, written in the notebook | No |

The price file is never in GitHub (D-004).

## Main flows

### Extract the prices (once)

1. The student runs `scripts/fetch_prices.py` on their machine.
2. It writes the price file and prints its checksum.
3. The student uploads the file to Drive, shares it by link, and gives the file ID and checksum to the notebook.

### The evaluator runs the notebook

1. Run all in a fresh free Colab runtime.
2. The setup cell installs the solvers and the package at the pinned tag.
3. The data cell downloads the file with gdown and stops with a Portuguese message if the checksum differs.
4. The notebook formulates the model, solves it with CBC, Ipopt and Couenne, runs the genetic algorithm, and prints the gap.

### The student runs an experiment

1. Change the `PARAMS` cell and use Run all.
2. Compare the new results with the previous ones.

## Security and privacy

- No personal data and no company data.
- No keys or secrets. The Drive file is public prices only, shared by link.
- The repository holds no data.

## Decisions behind it

- D-001 · Use public crypto price data, not the company data
- D-002 · Which public source of crypto prices
- D-003 · Delivery and run environment: Google Colab
- D-004 · Where the price data lives for the Colab delivery
- D-005 · Two deliverables: a Colab notebook and a portfolio repository
- D-006 · How the notebook and the repository share one codebase

## Open points

| Nº | Point | Depends on |
|---|---|---|
| 1 | The folder name of the project inside github.com/erickcmendes/CEUB, and how that repository is organised | Task 01-03 |
| 2 | Whether Couenne and Ipopt install in a fresh Colab runtime, in one setup cell | T-002 |
| 3 | The repository must be public, and the tag must exist, when the evaluator runs the notebook | The student, T-005 |
| 4 | Defaults of the formulation (about 20 assets, window 2021 to 2025, cardinality 5, weights between 5% and 40%, CVaR level 95%). They are deduced and the student can change any of them | Task 02-01 |
