# System description

**Project:** crypto-portfolio-optimization · **Version:** 0.2 · **Date:** 2026-10-16

> **In short:** Python code and a written analysis that formulate and solve a crypto portfolio selection problem with exact solvers and a metaheuristic, using public daily price data. In A2 it adds an ML forecasting pipeline. One student builds it for the course Optimização Aplicada à Ciência de Dados (CEUB, Prof. Danilo Silva). A1 is due 2026-10-19 and A2 on 2026-12-07.

## What it is

A coursework project that formulates, implements, solves and critically analyses a complex optimization problem tied to a real Data Science and ML scenario. The scenario is choosing which crypto assets to hold, and in what proportion, from a candidate universe, under a limit on how many assets can be held. The exact formulation is not fixed yet.

## Problem and value

- **The problem:** The course asks for a complex optimization problem that combines exact methods (Pyomo or PuLP with CBC, Ipopt, Couenne) and approximate ones (genetic algorithm with DEAP, or Simulated Annealing).
- **Who has it:** The student, who must deliver it, and the evaluator, who must be able to judge it.
- **How it is handled today:** Nothing built yet.
- **What changes with the product:** A formal model, a reproducible implementation and a critical comparison between exact and approximate solutions.

## Who uses it

| Who | What they need |
|---|---|
| The student (author) | Run experiments, change parameters, write the report, and explain the work in class |
| The evaluator (Prof. Danilo Silva) | Read the formulation, the code and the analysis, run it in Colab, and trust the results |

## Goals and success

1. Deliver A1, stages 1 to 3 (formal formulation, exact solution, metaheuristic), by 2026-10-19.
2. Deliver A2, stages 4 and 5 (ML integration, comparative analysis), by 2026-12-07.
3. Do it as a high-level project with software engineering rigor.

**How we will know it worked:** the student asked for "high level and software engineering rigor". The acceptance criteria are still to be settled in the requirements.

## How it reaches people

A Google Colab link to Python notebooks, with the analysis written inside them in Portuguese. The evaluator opens the link and runs everything. The student's portfolio repository, github.com/erickcmendes/CEUB, holds a thin, professional version of the project, and not the data.

## Scope

- **In the first version (A1):** formal formulation, exact solution with solvers, metaheuristic solution.
- **Out of the first version:** stages 4 and 5 (A2); ML forecasting; any user interface, live trading or investment advice (deduced).
- **Later:** A2, due 2026-12-07.

## Limits and context

- **Limits the person declared:** the two deadlines; works alone; documents in English and notebook text in Portuguese; only legal data, so public data and no personal data; tools named in the course PDF.
- **Systems to connect to or replace:** none.
- **Decided by the agent:** the project lives in its own folder, crypto-portfolio-optimization, inside the course folder; documents go in docs/ and task specs in docs/specs/; the company data in dados/ is left out (D-001).

## Open points

| Nº | Point | Depends on |
|---|---|---|
| 1 | Where the price data lives so the evaluator's Colab runtime finds it | D-004 |
| 2 | Overlap with the student's earlier crypto portfolio work in another course | The student and the professor |
| 3 | Yahoo Finance terms of use for the extracted prices, and whether the extraction works | The student, T-001 and T-004 |
