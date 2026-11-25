# Dashboard and A2 notebook

**Phase:** 4 · A2 · **Situation:** delivered, waiting for the student's test

## What it does

Course stage 6 (added in the A2 statement): an interactive dashboard of the project's metrics and goals, and the Portuguese Colab notebook that runs stages 4, 5 and 6 with one Run all.

## What it does not do

It does not change the A1 notebook. It does not deploy the dashboard anywhere: it is one HTML file.

## Done when

- [ ] `notebooks/a2_colab_pt.ipynb` runs top to bottom in a fresh Colab runtime
- [ ] `reports/dashboard_a2.html` is generated and opens in a browser
- [ ] The written discussion of stage 5 is in the notebook

## Comes from

FR-09 (stage 6), FR-05 (one Run all), FR-07, FR-08.

## Result of the delivery

2026-11-24 (Claude Code):
- `src/portfolio_opt/dashboard.py`: Plotly figures and a self-contained HTML file with key indicators, light and dark themes, and a validated colour palette.
- `notebooks/a2_colab_pt.ipynb`, generated and executed locally with the real solvers.
- `reports/dashboard_a2_referencia.html`: the dashboard of the reference run.

## How to test

Open the notebook in Colab and run all: in about 6 to 10 minutes, no cell should fail and section 6 should print the path of `reports/dashboard_a2.html`. Download that file and open it in a browser. Riskiest places first:
1. The setup cell: the solver install and the `v0.2.0` tag must exist on GitHub.
2. The Plotly CDN: the dashboard needs internet to load the library.
