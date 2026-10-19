# Cryptocurrency Portfolio Optimization

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/erickcmendes/CEUB/blob/main/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/a1_colab_pt.ipynb)

Coursework optimization project for **Otimização Aplicada à Ciência de Dados** (CEUB).

This project implements mathematical programming and metaheuristics for cryptocurrency portfolio selection under realistic constraints (cardinality limits, asset bounds, and scenario-based risk metrics).

---

## Overview

The portfolio problem is formulated and solved through two complementary paradigms:
1. **Exact Mathematical Programming (Pyomo):**
   - **Linear / Mixed-Integer Linear (MILP):** CVaR (Conditional Value at Risk) minimization solved via **COIN-OR CBC**.
   - **Continuous Nonlinear Programming (NLP):** Classical Markowitz mean-variance portfolio solved via **Ipopt**.
   - **Mixed-Integer Nonlinear Programming (MINLP):** Mean-variance portfolio with explicit cardinality limits and minimum lot constraints solved via **Couenne**.
2. **Metaheuristics (DEAP):**
   - **Genetic Algorithm (GA):** Evolutionary search tailored for non-convex MINLP cardinality-constrained optimization, featuring repair operators for budget and asset bounds, tournament selection, and elitism.

---

## Google Colab Notebooks

| Notebook | Descrição | Link Direto |
|---|---|---|
| **A1 Avaliação Principal** | Notebook completo com formulação, solvers exatos, AG, gráficos e tabela de Gap | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/erickcmendes/CEUB/blob/main/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/a1_colab_pt.ipynb) |
| **01 Solver Check** | Verificação de instalação automatizada do CBC, Ipopt e Couenne via IDAES | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/erickcmendes/CEUB/blob/main/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/01_solver_check_colab.ipynb) |

---

## Architecture

All optimization and data processing logic lives within the reusable Python package `portfolio_opt`:

```
crypto-portfolio-optimization/
├── src/portfolio_opt/
│   ├── params.py        # Central configuration (assets, cardinality, risk parameters, seeds)
│   ├── data.py          # Data ingestion, SHA-256 integrity check, scenario generation
│   ├── models.py        # Pyomo formulations (CVaR MILP, NLP, MINLP)
│   ├── solvers.py       # Solver orchestration and diagnostics
│   ├── ga.py            # DEAP genetic algorithm with constraint repair
│   └── metrics.py       # Portfolio performance metrics and optimality gap analysis
├── notebooks/
│   ├── 01_solver_check_colab.ipynb  # Verification notebook for CBC, Ipopt, Couenne in Colab
│   └── a1_colab_pt.ipynb            # Interactive Colab notebook for the evaluator
├── data/
│   └── crypto_prices.csv            # 27,740 price rows for 19 assets (2021-2024, SHA-256 verified)
├── scripts/
│   └── fetch_prices.py              # Yahoo Finance data extraction and checksum calculation
├── tests/                           # Automated test suite (pytest)
├── docs/                            # Blueprint specifications and architectural documents
└── pyproject.toml                   # Pinned dependencies and package configuration
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/erickcmendes/CEUB.git
cd "CEUB/Otimização para Ciência de Dados/crypto-portfolio-optimization"

# Install in editable mode
pip install -e .
```

---

## Running Tests

Execute the test suite verifying mathematical formulations, data rules, and genetic algorithm feasibility:

```bash
python -m pytest -v
```

---

## Evaluator Instructions (Google Colab)

The complete end-to-end evaluation pipeline can be run directly in Google Colab using `notebooks/a1_colab_pt.ipynb`. The notebook installs solvers automatically, retrieves the verified price snapshot, runs exact and metaheuristic models, and displays the comparative performance and optimality gaps.
