# Genetic algorithm

**Phase:** 2 · A1 core · **Situation:** not started

## What it does

`ga.py`: a DEAP genetic algorithm for the cardinality model, with the encoding, a repair step for the budget, cardinality and bounds, the fitness function, crossover, mutation, selection, population size and number of generations written in `PARAMS`, and a fixed seed.

## What it does not do

It does not forecast returns and it does not tune parameters automatically.

## Done when

- [ ] The same seed gives the same result
- [ ] Every solution it returns respects the constraints
- [ ] On the toy instance it finds the known optimum, or its gap is reported
- [ ] The encoding, operators and control parameters are documented in the module

## Comes from

FR-03, FR-06, NFR-01, acceptance criterion (c). Course PDF stage 3. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `src/portfolio_opt/ga.py` implementing a DEAP genetic algorithm for cardinality-constrained portfolio optimization. Features deterministic repair operator strictly enforcing cardinality, budget, and semi-continuous bounds, tournament selection with elitism, blend crossover, Gaussian mutation, parameter control via `PARAMS`, and fixed random seeds. Verified via `tests/test_ga.py`.

## How to test

Run `python -m pytest tests/test_ga.py`. All tests pass, proving that the repair operator strictly enforces all constraints, that runs with identical seeds yield identical results, and that convergence history is logged properly.
