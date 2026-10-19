# Interface contract

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-16

> **In short:** The evaluator opens the Colab link and uses Run all. The notebook installs the solvers, downloads and checks the price file, solves the problem, and shows the results. Parameters are changed in one cell. Failures stop the run with a message in Portuguese that names the cause.

## Who calls it

| Who | How they call it | What they expect |
|---|---|---|
| The evaluator | Opens the Colab link and uses Run all | The whole notebook runs from a fresh runtime with no error |
| The student | The same, after changing the parameters cell | The same notebook with new results |

## What is offered

| What | What it does | What it needs | What comes back |
|---|---|---|---|
| Run all | Installs the solvers, gets the data, formulates and solves the model, runs the genetic algorithm | A fresh Colab runtime and access to the shared price file | The formulation, the solutions of the three solvers, the genetic algorithm result and the gap to the optimum |
| `PARAMS` cell | Holds the main parameters, such as the cardinality limit, the risk setting, the random seed and the time window | Values in the cell | The next run uses them |

## When it fails

Deduced from the requirements. Each failure stops the run with a message in Portuguese.

| Failure | What the caller sees |
|---|---|
| A solver does not install or is not found | A message naming the solver |
| The price file cannot be downloaded | A message saying the download failed and where it tried |
| The checksum does not match | A message saying the file differs from the expected one |

## What never changes without warning

- The `PARAMS` cell and its parameter names, once the evaluator has seen them.
- Run all runs everything with no manual step.

## What is left out

- Any command line or user interface.
- Saving results outside the notebook outputs.
