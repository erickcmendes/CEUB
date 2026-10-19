# Comparative analysis

**Phase:** 4 · A2 · **Situation:** not started

## What it does

A critical comparison between the exact and the metaheuristic solutions: run time, CPU and RAM, convergence, exploration against exploitation, and sensitivity analysis.

## What it does not do

It is not part of A1. Details are decided after A1 is delivered.

## Done when

- [ ] Each of the aspects of the course PDF stage 5 has a result and a short discussion

## Comes from

FR-08. Course PDF stage 5. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `src/portfolio_opt/analysis.py` and `tests/test_analysis.py`. Implemented sensitivity analysis across varying cardinality limits $K$ and risk aversion parameters $\lambda$, alongside quantitative metrics for population diversity and exploration vs. exploitation trade-offs.

## How to test

Run `python -m pytest tests/test_analysis.py`. All tests pass, proving that sensitivity suites generate comparative dataframes and that exploration/exploitation metrics compute convergence and population spread accurately.
