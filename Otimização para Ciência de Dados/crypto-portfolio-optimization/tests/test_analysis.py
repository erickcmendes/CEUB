"""
# FR-08, Course PDF Stage 5: Tests for sensitivity analysis and exploration/exploitation metrics.
"""

import pytest
import numpy as np
import pandas as pd

from portfolio_opt.params import OptimizationParams
from portfolio_opt.ga import run_genetic_algorithm
from portfolio_opt.analysis import (
    run_cardinality_sensitivity,
    run_risk_aversion_sensitivity,
    compute_diversity_metrics,
)


@pytest.fixture
def test_env():
    """Deterministic market setup."""
    assets = ["BTC", "ETH", "SOL", "BNB"]
    cov_df = pd.DataFrame(
        np.array([
            [0.0004, 0.0002, 0.0001, 0.0001],
            [0.0002, 0.0005, 0.0002, 0.0002],
            [0.0001, 0.0002, 0.0006, 0.0001],
            [0.0001, 0.0002, 0.0001, 0.0004],
        ]),
        index=assets,
        columns=assets
    )
    mean_df = pd.Series([0.002, 0.003, 0.0025, 0.0015], index=assets)
    return cov_df, mean_df


def test_cardinality_sensitivity(test_env):
    """# FR-08: Verify cardinality sensitivity returns valid dataframe."""
    cov_df, mean_df = test_env
    df_k = run_cardinality_sensitivity(cov_df, mean_df, k_values=[2, 3])

    assert isinstance(df_k, pd.DataFrame)
    assert len(df_k) == 2
    assert "Cardinalidade (K)" in df_k.columns


def test_risk_aversion_sensitivity(test_env):
    """# FR-08: Verify risk aversion sensitivity produces profiles."""
    cov_df, mean_df = test_env
    df_lambda = run_risk_aversion_sensitivity(cov_df, mean_df, lambda_values=[0.2, 1.0])

    assert isinstance(df_lambda, pd.DataFrame)
    assert len(df_lambda) == 2
    assert "Lambda (Aversão)" in df_lambda.columns


def test_compute_diversity_metrics(test_env):
    """# FR-08: Verify exploration/exploitation diversity metrics."""
    cov_df, mean_df = test_env
    p = OptimizationParams(ga_pop_size=20, ga_generations=10, ga_seed=42)
    res = run_genetic_algorithm(cov_df, mean_df, p)

    div = compute_diversity_metrics(res)
    assert "convergence_rate_pct" in div
    assert "final_generation_spread" in div
