# Plan

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-17

> **In short:** Four phases and 12 tasks. A1 (phases 1 to 3, ten tasks) is due on Monday 2026-10-19, and A2 (phase 4) on 2026-12-07. The first task is the solver check in Colab, because it is the biggest risk. The formal formulation comes next, because everything else depends on it.

## How the work goes

- One task at a time, in the order below, except that the student's own steps (running the solver check, extracting the prices) happen in parallel with the work that does not depend on them.
- A task is delivered with how to test it: what to run or open, and what should be seen.
- The student marks a task as done after trying its test. The agent writes the result of the delivery in the spec.
- Proposed schedule, deduced: Saturday 17 phase 1 and the formulation; Sunday 18 the models, the genetic algorithm and the notebook; Monday 19 the release, a final run and the delivery.

## Phases

| Phase | What it delivers | Done when |
|---|---|---|
| 1 · Foundations | Solvers confirmed in Colab, the price file in Drive, the repository skeleton | T-001, T-002 and T-004 have a result, and `pytest` runs in the skeleton |
| 2 · A1 core | The formulation, the data layer, the exact models, the genetic algorithm and the gap | The three solvers and the genetic algorithm run on the real instance and tests pass |
| 3 · A1 delivery | The Colab notebook and the release | Run all passes in a private window, and the link is submitted |
| 4 · A2 | The ML forecast integration and the comparative analysis | The two course stages of A2 are written and reproducible |

## Tasks

### Phase 1 · Foundations

1. Solver check in Colab: install CBC, Ipopt and Couenne in one cell and solve a toy problem. Spec: `specs/01-01-solver-check-colab.md`
2. Extract the prices: the yfinance script, the price file and its checksum. Spec: `specs/01-02-extract-prices.md`
3. Repository skeleton: the project folder in github.com/erickcmendes/CEUB. Spec: `specs/01-03-repository-skeleton.md`

### Phase 2 · A1 core

1. Formal formulation: three models written in mathematics. Spec: `specs/02-01-formulation.md`
2. Data layer: loading, checksum, returns, covariance and scenarios. Spec: `specs/02-02-data-layer.md`
3. Exact models: Pyomo models solved by CBC, Ipopt and Couenne. Spec: `specs/02-03-exact-models.md`
4. Genetic algorithm: DEAP, with repair and a fixed seed. Spec: `specs/02-04-genetic-algorithm.md`
5. Comparison and gap: the table and the gap to the exact optimum. Spec: `specs/02-05-comparison-and-gap.md`

### Phase 3 · A1 delivery

1. Colab notebook: the Portuguese notebook that installs and runs the package. Spec: `specs/03-01-colab-notebook.md`
2. Release and delivery: tag, public repository, shared file, final run, submit. Spec: `specs/03-02-release-and-delivery.md`

### Phase 4 · A2

1. ML forecast integration: forecasts feed the optimizer. Spec: `specs/04-01-ml-forecast.md`
2. Comparative analysis: time, convergence, exploration and sensitivity. Spec: `specs/04-02-comparative-analysis.md`

## What depends on people

- The student runs task 1.1 in Colab, because only they can open it. It decides whether Couenne is usable.
- The student runs task 1.2 on their machine, uploads the file to Drive and shares it by link, and reads the Yahoo terms of use.
- The student gives access to github.com/erickcmendes/CEUB before task 1.3.
- The student reviews the defaults of the formulation in task 2.1.
- The student makes the repository public and submits the link in task 3.2.
- The role of the ML model is still open and is needed before phase 4.
