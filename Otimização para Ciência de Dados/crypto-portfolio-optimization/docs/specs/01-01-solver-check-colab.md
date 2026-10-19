# Check the solvers in Colab

**Phase:** 1 · Foundations · **Situation:** not started

## What it does

A small Colab notebook that installs CBC, Ipopt and Couenne in one setup cell, solves a toy Pyomo problem with each, and prints the Python version, the solver versions and the install time.

## What it does not do

It does not build the real models and it does not install the project package.

## Done when

- [ ] The setup cell runs from a fresh Colab runtime with no manual step
- [ ] CBC, Ipopt and Couenne each solve the toy problem and report an optimal status
- [ ] The Python version and the install time are written down in the test plan (T-002)

## Comes from

NFR-02, FR-02, D-003, T-002. The student runs it, because only they can open Colab. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Created `notebooks/01_solver_check_colab.ipynb` containing automated installation of CBC, Ipopt and Couenne via IDAES binary extensions (`idaes get-extensions`) and Pyomo toy problem formulations for each solver class.

## How to test

Open `notebooks/01_solver_check_colab.ipynb` in Google Colab, select 'Run all', and verify that:
1. IDAES binaries are downloaded and installed.
2. CBC, Ipopt and Couenne each solve their respective toy problems reporting optimal status.
3. Execution time and Python version are displayed.
