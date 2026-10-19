# Exact models

**Phase:** 2 · A1 core · **Situation:** not started

## What it does

`models.py` and `solvers.py`: the three Pyomo models of the formulation, solved by CBC, Ipopt and Couenne, with status checks, timing and a clear message when a solver is missing. Tests use a toy instance with a known optimum.

## What it does not do

It does not run the genetic algorithm and it does not compare the methods.

## Done when

- [ ] Each model solves the toy instance to the known optimum
- [ ] A missing solver gives a message that names it
- [ ] Results are the same on two runs
- [ ] The three solvers run on the real instance, or the limit of each is written down

## Comes from

FR-02, NFR-01, D-003, T-002. Course PDF stage 2. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `src/portfolio_opt/models.py` (CVaR MILP, Mean-Variance NLP, Cardinality MINLP) and `src/portfolio_opt/solvers.py` (safe solver availability check, execution wrapper with timing and Portuguese error messages for missing solvers). Verified via `tests/test_models.py`.

## How to test

Run `python -m pytest tests/test_models.py`. All tests pass verifying algebraic model structure, index sets, variable bounds, semi-continuous constraints, and solver error handling.
