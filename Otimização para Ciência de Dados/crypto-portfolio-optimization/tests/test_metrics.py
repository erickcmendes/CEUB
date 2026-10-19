"""
# FR-04, acceptance criterion (c): Tests for performance metrics, risk measures, optimality gap, and summary table.
"""

import pytest
import numpy as np
import pandas as pd

from portfolio_opt.metrics import (
    compute_portfolio_metrics,
    compute_optimality_gap,
    build_comparison_summary,
)
from portfolio_opt.solvers import OptimizationResult
from portfolio_opt.ga import GAResult


@pytest.fixture
def market_context():
    """Deterministic return and covariance fixtures."""
    assets = ["BTC", "ETH"]
    # 5 daily scenarios
    scenarios = pd.DataFrame(
        [
            [0.01, 0.02],
            [-0.02, 0.01],
            [0.03, -0.01],
            [-0.01, 0.04],
            [0.02, 0.01],
        ],
        columns=assets
    )
    mean_ret = scenarios.mean()
    cov_mat = scenarios.cov()
    return scenarios, cov_mat, mean_ret


def test_compute_portfolio_metrics(market_context):
    """# FR-04: Test calculation of return, annualization, volatility, VaR, and CVaR."""
    scenarios, cov_mat, mean_ret = market_context
    weights = {"BTC": 0.5, "ETH": 0.5}

    metrics = compute_portfolio_metrics(weights, scenarios, cov_mat, mean_ret, alpha=0.80)

    assert "daily_return" in metrics
    assert "annual_return" in metrics
    assert "daily_volatility" in metrics
    assert "annual_volatility" in metrics
    assert "sharpe_ratio" in metrics
    assert "var_95" in metrics
    assert "cvar_95" in metrics
    # CVaR >= VaR always holds mathematically
    assert metrics["cvar_95"] >= metrics["var_95"] - 1e-6


def test_compute_optimality_gap():
    """# FR-04, acceptance criterion (c): Verify optimality gap calculation."""
    # When heuristic equals exact, gap is 0%
    assert compute_optimality_gap(10.0, 10.0) == 0.0
    # Exact = 100, Heuristic = 105 -> Gap = 5%
    assert np.isclose(compute_optimality_gap(105.0, 100.0), 5.0)


def test_build_comparison_summary(market_context):
    """# FR-04: Verify consolidated summary table generation across solver and GA results."""
    scenarios, cov_mat, mean_ret = market_context

    exact_res = OptimizationResult(
        model_name="Cardinality_MINLP_Couenne",
        solver_name="couenne",
        status="ok",
        termination_condition="optimal",
        objective_value=0.000150,
        weights={"BTC": 0.6, "ETH": 0.4},
        solve_time_sec=1.25,
        is_optimal=True,
    )

    ga_res = GAResult(
        best_weights={"BTC": 0.55, "ETH": 0.45},
        best_objective=0.000155,
        portfolio_return=0.0015,
        portfolio_variance=0.0003,
        portfolio_volatility=0.0173,
        execution_time_sec=0.85,
    )

    df_summary = build_comparison_summary(
        [exact_res, ga_res],
        returns_matrix=scenarios,
        cov_matrix=cov_mat,
        mean_returns=mean_ret,
        exact_reference_solver="couenne",
    )

    assert isinstance(df_summary, pd.DataFrame)
    assert len(df_summary) == 2
    assert "Método / Solver" in df_summary.columns
    assert "Gap vs Ótimo" in df_summary.columns
    assert "CVaR 95% Diário (%)" in df_summary.columns
