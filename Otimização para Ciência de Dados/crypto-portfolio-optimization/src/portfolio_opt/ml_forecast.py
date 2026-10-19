"""
# FR-07, Course PDF Stage 4
Machine Learning Return Forecasting Pipeline and Out-of-Sample Portfolio Evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, ElasticNet


@dataclass
class ForecastComparisonResult:
    """Comparison metrics between naive historical mean allocation and ML-forecasted allocation."""
    historical_weights: Dict[str, float]
    ml_weights: Dict[str, float]
    out_of_sample_return_hist: float
    out_of_sample_return_ml: float
    out_of_sample_vol_hist: float
    out_of_sample_vol_ml: float
    out_of_sample_sharpe_hist: float
    out_of_sample_sharpe_ml: float
    improvement_sharpe_pct: float


def build_asset_features(
    asset_returns: pd.Series,
    lags: List[int] = [1, 2, 3, 5],
    vol_window: int = 7,
    mom_window: int = 7,
) -> Tuple[pd.DataFrame, pd.Series]:
    """# FR-07: Construct predictive features (lags, rolling volatility, momentum) and next-day target."""
    df_feat = pd.DataFrame(index=asset_returns.index)

    # Autoregressive lags
    for lag in lags:
        df_feat[f"lag_{lag}"] = asset_returns.shift(lag)

    # Rolling volatility
    df_feat["rolling_vol"] = asset_returns.rolling(window=vol_window).std()

    # Momentum (cumulative return over window)
    df_feat["momentum"] = asset_returns.rolling(window=mom_window).sum()

    # Target: 1-step-ahead daily return
    target = asset_returns.shift(-1)

    # Clean missing boundary rows
    valid_idx = ~(df_feat.isna().any(axis=1) | target.isna())
    return df_feat.loc[valid_idx], target.loc[valid_idx]


def forecast_expected_returns(
    returns_matrix: pd.DataFrame,
    model_type: str = "ridge",
    regularization_alpha: float = 1.0,
) -> pd.Series:
    """# FR-07: Train supervised regression models per asset to forecast next-period expected returns.

    Returns:
        pd.Series: Vector \\hat{\\mu}_{t+1} of forecasted expected returns.
    """
    forecasts = {}
    assets = list(returns_matrix.columns)

    for asset in assets:
        s_ret = returns_matrix[asset]
        X, y = build_asset_features(s_ret)

        if len(X) < 30:
            # Fallback to historical mean if sample too small
            forecasts[asset] = float(s_ret.mean())
            continue

        if model_type.lower() == "elasticnet":
            model = ElasticNet(alpha=regularization_alpha, l1_ratio=0.5, random_state=42)
        else:
            model = Ridge(alpha=regularization_alpha, random_state=42)

        model.fit(X, y)

        # Predict next-day return using most recent available feature vector
        latest_features = X.iloc[[-1]]
        pred = float(model.predict(latest_features)[0])

        # Shrinkage guard: avoid extreme unfeasible extrapolation
        hist_mean = float(s_ret.mean())
        hist_std = float(s_ret.std())
        clipped_pred = np.clip(pred, hist_mean - 3 * hist_std, hist_mean + 3 * hist_std)

        forecasts[asset] = float(clipped_pred)

    return pd.Series(forecasts)


def run_out_of_sample_ml_comparison(
    returns_matrix: pd.DataFrame,
    train_ratio: float = 0.80,
    top_k: int = 5,
    min_w: float = 0.05,
    max_w: float = 0.40,
) -> ForecastComparisonResult:
    """# FR-07, Course PDF Stage 4: Out-of-sample backtest comparing naive historical mean vs ML-forecast allocation."""
    n_rows = len(returns_matrix)
    split_idx = int(n_rows * train_ratio)

    train_returns = returns_matrix.iloc[:split_idx]
    test_returns = returns_matrix.iloc[split_idx:]

    # 1. Baseline: Expected returns = In-sample Historical Mean
    hist_mu = train_returns.mean()

    # 2. ML Forecast: Ridge regression predictions
    ml_mu = forecast_expected_returns(train_returns, model_type="ridge")

    def _allocate_top_k(mu_vec: pd.Series) -> Dict[str, float]:
        """Simple deterministic allocation: pick top K expected returns and allocate uniformly."""
        best_assets = mu_vec.sort_values(ascending=False).head(top_k).index.tolist()
        w = 1.0 / len(best_assets)
        return {a: w for a in best_assets}

    hist_weights = _allocate_top_k(hist_mu)
    ml_weights = _allocate_top_k(ml_mu)

    # Evaluate out-of-sample performance
    def _eval_portfolio(weights_dict: Dict[str, float]) -> Tuple[float, float, float]:
        w_vec = np.array([weights_dict.get(a, 0.0) for a in test_returns.columns])
        port_daily = test_returns.values @ w_vec
        daily_mean = float(np.mean(port_daily))
        daily_vol = float(np.std(port_daily))
        annual_ret = daily_mean * 365.0
        annual_vol = daily_vol * np.sqrt(365.0)
        sharpe = annual_ret / annual_vol if annual_vol > 1e-8 else 0.0
        return annual_ret, annual_vol, sharpe

    ann_ret_hist, ann_vol_hist, sharpe_hist = _eval_portfolio(hist_weights)
    ann_ret_ml, ann_vol_ml, sharpe_ml = _eval_portfolio(ml_weights)

    improvement = (
        ((sharpe_ml - sharpe_hist) / abs(sharpe_hist)) * 100.0
        if abs(sharpe_hist) > 1e-6
        else 0.0
    )

    return ForecastComparisonResult(
        historical_weights=hist_weights,
        ml_weights=ml_weights,
        out_of_sample_return_hist=round(ann_ret_hist, 4),
        out_of_sample_return_ml=round(ann_ret_ml, 4),
        out_of_sample_vol_hist=round(ann_vol_hist, 4),
        out_of_sample_vol_ml=round(ann_vol_ml, 4),
        out_of_sample_sharpe_hist=round(sharpe_hist, 4),
        out_of_sample_sharpe_ml=round(sharpe_ml, 4),
        improvement_sharpe_pct=round(improvement, 2),
    )
