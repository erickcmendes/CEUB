# Comparison and gap

**Phase:** 2 · A1 core · **Situation:** not started

## What it does

`metrics.py`: return, risk and CVaR of a solution, and the gap between the genetic algorithm and the exact optimum, in a table the notebook prints.

## What it does not do

The full critical analysis with convergence, sensitivity and CPU and RAM belongs to A2.

## Done when

- [ ] The gap is computed against the Couenne optimum, and against the best known bound when Couenne does not finish
- [ ] A table shows the objective, the chosen assets, the weights and the time of each method

## Comes from

FR-04, acceptance criterion (c). These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `src/portfolio_opt/metrics.py` and `tests/test_metrics.py`. Computes daily and annualized expected return, volatility, Sharpe ratio, historical VaR, scenario CVaR, relative optimality gap against exact MINLP benchmarks, and consolidated comparative summary tables.

## How to test

Run `python -m pytest tests/test_metrics.py`. All tests pass, validating risk calculations, CVaR/VaR inequality properties, gap percentages, and summary table formatting across solvers and metaheuristics.
