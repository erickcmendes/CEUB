# Comparative analysis

**Phase:** 4 · A2 · **Situation:** delivered, waiting for the student's test

## What it does

A critical comparison between the exact and the metaheuristic solutions: run time, CPU and RAM, convergence, exploration against exploitation, and sensitivity analysis.

## What it does not do

It is not part of A1. Details are decided after A1 is delivered.

## Done when

- [ ] Each of the aspects of the course PDF stage 5 has a result and a short discussion

## Comes from

FR-08. Course PDF stage 5. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

2026-10-18 (Antigravity): `analysis.py` with GA-only sensitivity, kept for its tests.

2026-11-24 (Claude Code): `src/portfolio_opt/evaluation.py`. It covers:
- `profile_call`: wall and CPU time including the solver child processes, peak RSS of the solver process, Python heap via tracemalloc.
- Couenne (exact) against the Ipopt continuous relaxation (lower bound), the GA over 10 seeds and CBC.
- Convergence tables, a grid of mutation σ × tournament size, and sensitivity to K, λ and N.

The GA now logs population diversity and flags infeasible results (`is_feasible`). Two solver bugs fixed in `solvers.py`: the availability check always returned False, and Couenne's time limit was rejected. The written discussion is section 5.3 of the A2 notebook.

## How to test

Run `python -m pytest tests/test_a2_pipeline.py -k fr08` with the solvers on the PATH, then open section 5 of the notebook. Riskiest places, hardest first:
1. `check_solver_available` in `solvers.py`, because it silently disabled the exact solvers (covered by `test_fr02_solver_check_matches_executable_on_path`).
2. The CPU measurement of child processes in `profile_call`: Windows does not report waited children, so it falls back to sampling.
3. The gap is shown as missing when K makes the problem infeasible.
