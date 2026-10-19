# AI Features: Machine Learning Forecasting for Portfolio Optimization

**Project:** crypto-portfolio-optimization  
**Phase:** 4 · A2  
**Requirement:** `FR-07`, `Course PDF Stage 4`

---

## 1. Executive Summary

In traditional Markowitz and CVaR models, expected asset returns $\boldsymbol{\mu}$ are estimated using naive historical sample means. In highly dynamic markets like cryptocurrencies, historical means suffer from high estimation error, leading to the well-known "error-maximization" property of mean-variance optimizers (Michaud, 1989).

Stage 4 introduces a Machine Learning return forecasting pipeline that replaces naive historical means with predictive expected return estimates $\hat{\boldsymbol{\mu}}_{t+1}$, assessing the resulting impact on out-of-sample portfolio risk and return.

---

## 2. Predictive Architecture

```
Historical Prices (Daily)
        │
        ▼
Feature Engineering (Lags, Rolling Volatility, Momentum, EMA)
        │
        ▼
Walk-Forward / Rolling-Window Train/Test Split
        │
        ▼
Forecasting Models:
  1. Ridge Regression (L2 Regularization)
  2. ElasticNet (L1 + L2 Regularization)
  3. Random Forest Regressor (Non-linear capture)
        │
        ▼
Predicted Expected Returns Vector (\hat{\mu}_{t+1})
        │
        ▼
Portfolio Optimization Engine:
  - Exact Solvers (CBC, Ipopt, Couenne)
  - Metaheuristic (DEAP Genetic Algorithm)
        │
        ▼
Out-of-Sample Performance Comparison:
  - Cumulative Wealth & Return
  - Out-of-Sample Sharpe Ratio
  - Maximum Drawdown
  - Tail Risk (Realized CVaR 95%)
```

---

## 3. Feature Engineering Specification

For each asset $i$ on day $t$:
1. **Lags:** $r_{i, t-1}, r_{i, t-2}, r_{i, t-3}, r_{i, t-5}$.
2. **Rolling Volatility:** 7-day and 30-day standard deviation of returns.
3. **Momentum:** 7-day and 14-day cumulative return.
4. **Target:** 1-step-ahead daily return $r_{i, t+1}$.

---

## 4. Failure Modes and Fallback Mechanism

- **Stationarity and Covariance Shifts:** When ML predictions predict extreme outliers (e.g. $|\hat{\mu}| > 30\%$ daily), predictions are winsorized/clipped to historical $\pm 3\sigma$.
- **Model Disagreement:** If out-of-sample MSE of the model exceeds baseline historical mean variance on the validation window, a shrinkage combination $\hat{\boldsymbol{\mu}}_{comb} = \delta \hat{\boldsymbol{\mu}}_{ML} + (1 - \delta) \bar{\boldsymbol{\mu}}_{hist}$ (Ledoit-Wolf shrinkage philosophy) is applied.
