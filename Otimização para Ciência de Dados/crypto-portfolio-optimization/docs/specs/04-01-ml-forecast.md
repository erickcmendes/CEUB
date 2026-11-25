# ML forecast integration

**Phase:** 4 · A2 · **Situation:** delivered, waiting for the student's test

## What it does

A forecasting model feeds expected returns to the optimizer, and the notebook shows the impact on predictive or operational performance. The role of the model is defined first, in the `ai-features` document.

## What it does not do

It is not part of A1. Details are decided after A1 is delivered.

## Done when

- [ ] The `ai-features` document is written and the student agreed to it
- [ ] The impact of the forecast on the optimized portfolio is measured out of sample

## Comes from

FR-07. Course PDF stage 4. Open: the model's role, a main question of modeling. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

2026-10-18 (Antigravity): `ml_forecast.py` with per-asset Ridge forecasts and a top-K equal-weight comparison. That version did not feed the optimizer and lost to the historical mean out of sample.

2026-11-24 (Claude Code): `src/portfolio_opt/backtest.py`. Walk-forward pipeline, rebalancing every 30 days from 2022-01 to 2024-12 (37 decisions). A pooled Ridge model, trained only on targets already realized, forecasts the next 30-day mean return. The forecast feeds the GA optimizer (K=5), and the result is compared with the historical mean (A1), a minimum-variance control (μ=0), 1/N and BTC, with a 0.1% cost on turnover. Predictive metrics: RMSE, MAE, direction and Spearman IC. Result: ML beats the historical mean (Sharpe 0.20 vs −0.12), but the forecast has no predictive power (IC ≈ 0) and the min-variance control wins (Sharpe 0.80). Details are in `docs/a2-handoff.md` and in section 4 of the A2 notebook.

## How to test

Run `python -m pytest tests/test_a2_pipeline.py -k fr07`. Then open `notebooks/a2_colab_pt.ipynb`, section 4: the performance table has 5 strategies and the robustness table shows ML above the historical mean for every Ridge alpha. Riskiest place first: `train_and_forecast` in `backtest.py`, because a look-ahead bug there would invalidate the whole stage (covered by `test_fr07_forecast_has_no_look_ahead`).
