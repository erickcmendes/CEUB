"""
# FR-07, Course PDF Stage 4: Tests for Machine Learning forecasting pipeline and out-of-sample comparison.
"""

import pytest
import numpy as np
import pandas as pd

from portfolio_opt.ml_forecast import (
    build_asset_features,
    forecast_expected_returns,
    run_out_of_sample_ml_comparison,
)


@pytest.fixture
def synthetic_market():
    """Generates synthetic price returns across 60 days for 3 assets."""
    np.random.seed(42)
    days = 60
    assets = ["BTC", "ETH", "SOL"]
    data = np.random.normal(0.001, 0.02, size=(days, len(assets)))
    df = pd.DataFrame(data, columns=assets)
    return df


def test_build_asset_features(synthetic_market):
    """# FR-07: Verify feature creation contains lags, volatility, and target."""
    s_btc = synthetic_market["BTC"]
    X, y = build_asset_features(s_btc, lags=[1, 2], vol_window=5, mom_window=5)

    assert not X.empty
    assert len(X) == len(y)
    assert "lag_1" in X.columns
    assert "lag_2" in X.columns
    assert "rolling_vol" in X.columns
    assert "momentum" in X.columns


def test_forecast_expected_returns(synthetic_market):
    """# FR-07: Verify Ridge forecast returns a valid series of expected returns."""
    preds = forecast_expected_returns(synthetic_market, model_type="ridge")

    assert isinstance(preds, pd.Series)
    assert set(preds.index) == set(synthetic_market.columns)
    assert not preds.isna().any()


def test_out_of_sample_ml_comparison(synthetic_market):
    """# FR-07: Verify out-of-sample comparison executes and computes Sharpe ratios."""
    res = run_out_of_sample_ml_comparison(synthetic_market, train_ratio=0.7, top_k=2)

    assert res.out_of_sample_return_hist is not None
    assert res.out_of_sample_return_ml is not None
    assert len(res.historical_weights) == 2
    assert len(res.ml_weights) == 2
