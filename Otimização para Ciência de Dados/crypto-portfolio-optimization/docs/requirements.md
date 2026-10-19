# Requirements

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-16

> **In short:** Python notebooks, delivered as a Google Colab link, that the evaluator reads and runs without errors. A1 must deliver a formal formulation, an exact solution with CBC, Ipopt and Couenne on a small instance, and a genetic algorithm whose gap to the exact optimum is reported. The text inside the notebooks is in Portuguese. A1 is due 2026-10-19, A2 on 2026-12-07.

## What the system is

A set of notebooks that formulate and solve a crypto portfolio selection problem under a cardinality limit, using public price data. It is used by the student, who runs experiments and explains the work in class, and by the evaluator, who reads and runs the code in Colab.

## Functional requirements

| Nº | Requirement | Priority | Comes from |
|---|---|---|---|
| FR-01 | The formal formulation (sets, indices, parameters, continuous, integer and binary decision variables, objective, equality and inequality constraints) is written in a notebook and matches the implementation | First version (A1) | Course PDF, stage 1; acceptance criterion (a) |
| FR-02 | The exact model is implemented in Pyomo or PuLP and solved on a small instance with CBC, Ipopt and Couenne | First version (A1) | Course PDF, stage 2; acceptance criterion (b) |
| FR-03 | A genetic algorithm in DEAP solves the same problem, with the encoding, crossover, mutation, control parameters and fitness function documented | First version (A1) | Course PDF, stage 3; acceptance criterion (c) |
| FR-04 | The gap between the genetic algorithm and the exact optimum is measured and reported | First version (A1) | Acceptance criterion (c) |
| FR-05 | One action (Run all in Colab) reproduces the A1 results from a fresh runtime. If there is more than one notebook, each one runs from top to bottom without errors in Colab | First version (A1) | The student, 2026-10-16 |
| FR-06 | The main parameters (such as the cardinality limit and the risk setting) are changed in one place | First version (A1) | Deduced: the student reruns experiments |
| FR-07 | ML return forecasts feed the optimizer, and the impact on predictive or operational performance is shown | Later (A2) | Course PDF, stage 4 |
| FR-08 | The exact and the metaheuristic solutions are compared on run time, CPU and RAM, convergence, exploration against exploitation, and sensitivity | Later (A2) | Course PDF, stage 5 |

## Non-functional requirements

| Nº | Requirement | Priority | Comes from |
|---|---|---|---|
| NFR-01 | Reproducible: dependency versions pinned where Colab allows it, and random seeds fixed, so two runs give the same results | First version (A1) | Deduced from "software engineering rigor" |
| NFR-02 | Runs in Google Colab, on a fresh runtime, with the solvers installed by the notebook itself | First version (A1) | The student, 2026-10-16 |
| NFR-03 | The work is delivered as notebooks, and the text inside them is in Portuguese | First version (A1) | The student |
| NFR-04 | Only legal data: public, with no personal data, and its license or terms of use are recorded | First version (A1) | The student |
| NFR-05 | The price data is not in the GitHub repository. A fresh Colab runtime must still find it, through the shared Drive file | First version (A1) | The student; D-004 |
| NFR-06 | A thin, professional repository (package, tests, pinned dependencies, README) lives at github.com/erickcmendes/CEUB and shows the same project as portfolio | First version (A1), because the notebook installs the package from it (D-006). The student said they need both in the end | The student; D-005 |

## Limits

- Deadlines: A1 on 2026-10-19, A2 on 2026-12-07.
- One developer.
- Tools named by the course PDF: Pyomo or PuLP, CBC, Ipopt, Couenne, DEAP or Simulated Annealing.
- The portfolio repository is github.com/erickcmendes/CEUB, which already exists.

## Out of the first version

- Stages 4 and 5 of the course (A2).
- Any user interface, live trading or investment advice.

## How we will know it worked

Accepted by the student on 2026-10-15, for A1:
(a) the formulation is complete and consistent with the course PDF;
(b) the exact model is solved by the three solvers on a small instance and is reproducible with one command;
(c) the genetic algorithm runs and its gap to the optimum is measured and reported.

## Open points

| Nº | Point | Depends on |
|---|---|---|
| 1 | Whether Couenne, Ipopt and CBC install in a fresh Colab runtime, and which Python version Colab has | T-002 |
| 2 | Where the price data lives so that the evaluator's runtime finds it | D-004 |
| 3 | Yahoo Finance terms of use for the extracted prices, and whether the extraction works | T-001, T-004 |
| 4 | Maximum acceptable run time of Run all | The student |
| 5 | The repository must be public, and the pinned tag must exist, when the evaluator runs the notebook | The student, T-005 |
