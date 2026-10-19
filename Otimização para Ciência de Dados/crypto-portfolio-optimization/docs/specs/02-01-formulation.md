# Formal formulation

**Phase:** 2 · A1 core · **Situation:** not started

## What it does

`docs/formulation.md`, written in mathematics: sets and indices, fixed parameters, continuous, integer and binary decision variables, the objective and the equality and inequality constraints, for three models. A mixed-integer linear model that minimises CVaR (CBC). A continuous mean-variance model (Ipopt). The same with a cardinality limit and binaries (Couenne). It states the defaults of the architecture's open point 4.

## What it does not do

It does not implement anything and it does not choose the solver parameters.

## Done when

- [ ] Every symbol is defined once and used consistently
- [ ] Each of the three models lists variables by type, objective and constraints
- [ ] A reader can tell which model each solver receives
- [ ] The student reviewed the defaults and changed any they disagree with

## Comes from

FR-01, FR-02, acceptance criterion (a), D-006. Course PDF stage 1. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `docs/formulation.md`, providing explicit mathematical formulation for:
1. CVaR MILP model (CBC)
2. Mean-Variance NLP model (Ipopt)
3. Cardinality-constrained Mean-Variance MINLP model (Couenne)
4. Genetic Algorithm chromosome decoding and repair formulation (DEAP)

## How to test

Open `docs/formulation.md` and check that all sets, indices, parameters, decision variables (continuous, binary), objective functions, and constraints are defined unambiguously and mapped to their respective solvers.
