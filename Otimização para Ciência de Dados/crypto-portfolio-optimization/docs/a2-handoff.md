# A2 handoff · state on 2026-11-24 (afternoon)

A2 (stages 4, 5 and 6) is due **2026-12-07**. **The work is complete locally:** package code, tests (28/28), the Portuguese notebook `notebooks/a2_colab_pt.ipynb` (executed end to end with the real solvers, no errors, in about 6 min) and the dashboard `reports/dashboard_a2.html`. What is left depends on the student: publishing and the Colab check.

## Left for the student

1. Commit and push to `main` of github.com/erickcmendes/CEUB, then create and push the tag `v0.2.0` (the notebook pins it when it exists).
2. Open the A2 Colab link (in the README) and run all in a fresh runtime. Expect 6 to 10 minutes and no failing cell.
3. Submit the link. Optionally present with `reports/dashboard_a2.html`.
4. Recommended: rerun the A1 notebook, because the solver bug fixed here made it skip CBC, Ipopt and Couenne.

## Done (2026-11-24)

| File | What changed |
|---|---|
| `src/portfolio_opt/solvers.py` | **Bug fix (affects A1):** `available(exception_on_error=...)` is not a Pyomo keyword; the TypeError was swallowed and every solver looked unavailable, so the A1 notebook skipped CBC/Ipopt/Couenne. Now `exception_flag`. **Bug fix 2:** Couenne rejects `time_limit` on its command line; it is now written to a temporary `couenne.opt`. |
| `src/portfolio_opt/models.py` | MINLP start point clipped to `max_weight` (warning when 1/K > w_max). |
| `src/portfolio_opt/params.py` | `ga_mut_sigma`, `ga_mut_indpb` (exploration knobs). |
| `src/portfolio_opt/ga.py` | Per-generation diversity (`gene_std`, `unique_supports`); `GAResult.is_feasible`. |
| `src/portfolio_opt/backtest.py` (new) | FR-07 walk-forward pipeline: pooled Ridge forecast (no look-ahead) → GA optimizer, monthly rebalance, 0.1% cost; strategies ML, historical mean, min-variance control (μ=0), 1/N, BTC. Predictive metrics (RMSE, MAE, direction, Spearman IC). |
| `src/portfolio_opt/evaluation.py` (new) | FR-08: `profile_call` (wall, CPU incl. solver child processes, RAM via psutil, Python heap via tracemalloc); Couenne vs Ipopt relaxation (lower bound) vs GA over 10 seeds vs CBC; convergence; exploration grid (σ × tournament); sensitivity in K, λ, N. |
| `src/portfolio_opt/dashboard.py` (new) | FR-09 (stage 6): Plotly figures + self-contained HTML dashboard (light/dark). |
| `tests/test_a2_pipeline.py` (new) | 8 tests incl. no-look-ahead and the solver-check regression. **28/28 pass** with solvers on PATH. |
| `pyproject.toml`, `__init__.py` | version 0.2.0; deps `plotly`, `psutil`. |

Second part of the session: `notebooks/a2_colab_pt.ipynb` (generated, executed), `docs/specs/04-03-dashboard-and-notebook.md`, FR-09 in `docs/requirements.md`, task 04-03 in `docs/plan.md`, results in specs 04-01 and 04-02, A2 in the README. The sensitivity gap is now signed: when Couenne stops on its time limit (λ=0.25), its incumbent can be worse than the GA, and one run showed exactly that.

## Local environment used

A venv with Python 3.12, `idaes-pse` and `idaes get-extensions` (Windows binaries in `%LOCALAPPDATA%\idaes\bin`, add to PATH). Global Python 3.14 has no solvers and no psutil.

## Reference run (all numbers except times are deterministic)

**Baseline (K=5, λ=1):** Couenne optimal −0.0033932 (AVAX 5%, BNB 21%, DOGE 28%, SOL 40%, XRP 5%) in ~3 s; Ipopt relaxation −0.0033934 (lower bound, gap 0.0055%) in 0.16 s; GA best of 10 seeds gap 0.27%, mean 0.96% ± 1.02 (max 3.3%), ~1 s per run; **all 10 seeds found the same 5 assets as the optimum**. CBC (CVaR MILP) 0.0810 in 1.7 s. RAM: Couenne process ~16 MB, Ipopt ~8 MB, CBC ~33 MB, GA in-process ≈ 0.3 MB heap.

**Stage 4, out of sample 01/2022–12/2024, 37 rebalances:**

| Strategy | CAGR | Sharpe | Max DD | Final wealth | Turnover |
|---|---|---|---|---|---|
| Optimizer + ML (Ridge) | −10.6% | 0.20 | −86.0% | 0.72 | 1.02 |
| Optimizer + historical mean (A1) | −32.2% | −0.12 | −84.3% | 0.31 | 0.52 |
| **Optimizer min-variance (μ=0)** | **+35.0%** | **0.80** | −67.5% | **2.46** | 0.31 |
| Equal weight 1/N | −1.0% | 0.34 | −76.5% | 0.97 | 0.14 |
| BTC buy & hold | +25.1% | 0.68 | −66.7% | 1.96 | 0.03 |

Forecast quality: ML RMSE 0.00968 vs hist 0.00996; MAE 0.00739 vs 0.00716; direction 52.3% vs 53.9%; mean IC −0.025 vs +0.022; IC>0 in 38% vs 57% of months. Ridge alpha robustness (ML Sharpe): α=1 0.22, α=10 0.20, α=100 0.27 — always above hist, always below min-var. ML forecasts are *not* more compressed than the hist mean (std 0.0034 vs 0.0029), so do not claim a shrinkage effect.

Interpretation to write: neither forecast has reliable predictive power (IC ≈ 0, direction ≈ coin flip); the historical mean chased 2021 winners (SOL, AVAX, DOGE, NEAR in Jan/2022) into the 2022 crash; the control that ignores μ wins → the value of optimization here comes from the covariance structure, which is far more estimable than expected returns (Merton 1980, Michaud 1989, DeMiguel et al. 2009). The A1 in-sample optimum (179% expected annual return) is an "error maximizer" out of sample. Yearly: 2022 all lose (min-var −60%, BTC −65%, ML −85%); 2023 ML +190% best; 2024 min-var +159% best.

**Stage 5:**
- Convergence (seed 42): gap 19% at gen 1, 6.8% at gen 10, 3.7% at gen 40, 0.6% at gen 80; distinct asset sets in population 94 → ~20 by gen 20 (diversity collapse = shift to exploitation).
- Exploration grid (5 seeds, mean gap): σ=0.05 → 2.7–3.1% (premature convergence, low diversity); σ=0.2 → 2.1–2.7%, best single gaps 0.18%; σ=0.6 with tournament 2 → best mean 1.94%, but σ=0.6 + tournament 10 → 4.95% (too much disruption + too much pressure). Intermediate settings balance both.
- Sensitivity K (Couenne time grows 0.96 s → 3.4 s from K=3 to 10; GA flat ~1 s): GA gap 0.0% (K=3), 0.8, 1.7, 3.0, **9.7% (K=10)**. Cause: the repair operator always activates exactly K assets with ≥5% each, while the optimum keeps 5 assets even at K=10 → representation bias. **K=2 is infeasible** (2 × 40% < 100%): Couenne proves it; the GA silently returns a portfolio violating w_max (now flagged by `is_feasible`).
- Sensitivity λ: Couenne time 60 s **hitting the limit** at λ=0.25, 9.2 s at 0.5, 2.2 s at 1, 0.6 s at 2, 0.2 s at 4 (variance-dominated objective = weaker relaxation bounds, harder B&B). GA gap 8.6% at λ=4 (optimum has 3 assets, GA forced to 5). Risk-return frontier: vol 75%→125%, return 118%→197%.
- Sensitivity N (K=5): Couenne 0.3 → 1.9 s from N=5 to 19 (combinatorial growth); GA ~1 s flat.
- Timings on this Windows laptop were noisy in one run (identical GA runs took 1 s vs 14 s); rerun gave consistent numbers. Say in the notebook that times vary by machine.
