"""
# FR-01, FR-02, NFR-01, NFR-02: Tests for Pyomo model generation, constraints and solver diagnostics.
"""

import pytest
import pandas as pd
import numpy as np
import pyomo.environ as pyo

from portfolio_opt.params import OptimizationParams
from portfolio_opt.models import (
    build_cvar_milp_model,
    build_mean_variance_nlp_model,
    build_cardinality_minlp_model,
)
from portfolio_opt.solvers import check_solver_available, solve_pyomo_model


@pytest.fixture
def toy_market_data():
    """Generates deterministic toy return scenarios and covariance."""
    assets = ["BTC", "ETH", "SOL"]
    np.random.seed(42)
    # T=5 scenarios
    scenarios = pd.DataFrame(
        [
            [0.02, 0.03, -0.01],
            [-0.01, 0.04, 0.02],
            [0.01, -0.02, 0.01],
            [0.03, 0.01, -0.02],
            [-0.02, 0.02, 0.03],
        ],
        columns=assets
    )
    mean_ret = scenarios.mean()
    cov_mat = scenarios.cov()
    params = OptimizationParams(
        cardinality_limit=2,
        min_weight=0.10,
        max_weight=0.70,
        target_daily_return=0.005,
        cvar_alpha=0.90,
        risk_aversion_lambda=1.0,
    )
    return scenarios, mean_ret, cov_mat, params


def test_build_cvar_milp_structure(toy_market_data):
    """# FR-01, FR-02: Verify CVaR MILP model structure, variables, and constraints."""
    scenarios, mean_ret, _, params = toy_market_data
    model = build_cvar_milp_model(scenarios, mean_ret, params)

    assert isinstance(model, pyo.ConcreteModel)
    assert len(model.I) == 3
    assert len(model.S) == 5
    assert hasattr(model, "w")
    assert hasattr(model, "z")
    assert hasattr(model, "gamma")
    assert hasattr(model, "u")
    assert hasattr(model, "c_budget")
    assert hasattr(model, "c_target_return")
    assert hasattr(model, "c_cardinality")
    assert hasattr(model, "c_lb")
    assert hasattr(model, "c_ub")


def test_build_mean_variance_nlp_structure(toy_market_data):
    """# FR-01, FR-02: Verify continuous NLP Markowitz model structure."""
    _, mean_ret, cov_mat, params = toy_market_data
    model = build_mean_variance_nlp_model(cov_mat, mean_ret, params)

    assert isinstance(model, pyo.ConcreteModel)
    assert len(model.I) == 3
    assert hasattr(model, "w")
    assert hasattr(model, "c_budget")
    assert hasattr(model, "c_target_return")


def test_build_cardinality_minlp_structure(toy_market_data):
    """# FR-01, FR-02: Verify cardinality-constrained MINLP model structure."""
    _, mean_ret, cov_mat, params = toy_market_data
    model = build_cardinality_minlp_model(cov_mat, mean_ret, params)

    assert isinstance(model, pyo.ConcreteModel)
    assert len(model.I) == 3
    assert hasattr(model, "w")
    assert hasattr(model, "z")
    assert hasattr(model, "c_budget")
    assert hasattr(model, "c_cardinality")
    assert hasattr(model, "c_lb")
    assert hasattr(model, "c_ub")


def test_solver_missing_diagnostics(toy_market_data):
    """# NFR-02: Verify helpful Portuguese diagnostic when solver is missing."""
    _, mean_ret, cov_mat, params = toy_market_data
    model = build_mean_variance_nlp_model(cov_mat, mean_ret, params)

    fake_solver = "non_existent_solver_xyz"
    with pytest.raises(RuntimeError, match="não está disponível ou não foi encontrado"):
        solve_pyomo_model(model, fake_solver)
