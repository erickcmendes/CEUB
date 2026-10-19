# ML forecast integration

**Phase:** 4 · A2 · **Situation:** not started

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

Delivered `docs/ai-features.md`, `src/portfolio_opt/ml_forecast.py`, and `tests/test_ml_forecast.py`. Implemented autoregressive and rolling feature generation, regularized linear forecasting (Ridge/ElasticNet), expected return prediction vectors, and an out-of-sample backtest engine measuring the impact of forecast-driven allocations against naive historical mean allocations.

## How to test

Run `python -m pytest tests/test_ml_forecast.py`. All tests pass, verifying feature engineering, model training, prediction generation, and out-of-sample Sharpe ratio comparisons.
