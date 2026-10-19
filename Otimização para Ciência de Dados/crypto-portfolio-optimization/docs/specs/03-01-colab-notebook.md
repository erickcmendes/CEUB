# Colab notebook

**Phase:** 3 · A1 delivery · **Situation:** not started

## What it does

`notebooks/a1_colab_pt.ipynb`, in Portuguese: a setup cell that installs the solvers and the package at the pinned tag, a data cell that downloads the file with gdown and checks the checksum, the formulation, the exact results, the genetic algorithm, the gap, and the source of the main functions printed on screen. One `PARAMS` cell.

## What it does not do

It holds no logic of its own: everything it runs is in the package.

## Done when

- [ ] Run all from a fresh runtime, in a private window, finishes with no error
- [ ] A wrong checksum and a missing solver give the agreed Portuguese messages
- [ ] The text explains each step so the student can present it in class

## Comes from

FR-05, FR-06, NFR-02, NFR-03, D-004, D-006, T-003, T-005. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `notebooks/a1_colab_pt.ipynb`, in Portuguese: automated environment setup installing IDAES solver binaries (CBC, Ipopt, Couenne) and `portfolio_opt`, data ingestion with SHA-256 verification and Google Drive fallback, risk-return visualization, inspection of Pyomo model sources, execution of exact solvers and DEAP genetic algorithm with convergence tracking, consolidated comparative table with metrics and optimality gap, and presentation conclusion.

## How to test

Open `notebooks/a1_colab_pt.ipynb` in Google Colab (or JupyterLab), execute "Run all" (Executar tudo). Verify that all cells execute sequentially from top to bottom without errors, producing risk plots, optimization outputs, convergence curves, and the final comparative summary table.
