"""
# FR-03, FR-06, NFR-01, acceptance criterion (c): Tests for the DEAP Genetic Algorithm.
"""

import pytest
import numpy as np
import pandas as pd

from portfolio_opt.params import OptimizationParams
from portfolio_opt.ga import repair_and_decode_weights, run_genetic_algorithm


@pytest.fixture
def toy_market():
    """Deterministic market setup for GA testing."""
    assets = ["BTC", "ETH", "SOL", "BNB", "ADA"]
    cov_data = np.array([
        [0.0004, 0.0002, 0.0001, 0.0002, 0.0001],
        [0.0002, 0.0005, 0.0003, 0.0001, 0.0002],
        [0.0001, 0.0003, 0.0006, 0.0002, 0.0003],
        [0.0002, 0.0001, 0.0002, 0.0004, 0.0001],
        [0.0001, 0.0002, 0.0003, 0.0001, 0.0005],
    ])
    cov_df = pd.DataFrame(cov_data, index=assets, columns=assets)
    mean_df = pd.Series([0.002, 0.003, 0.0025, 0.0015, 0.001], index=assets)
    return cov_df, mean_df, assets


def test_repair_operator_constraints():
    """# FR-03: Verify that the repair operator strictly respects cardinality, budget, and box bounds."""
    assets = ["A", "B", "C", "D", "E"]
    individual = [0.9, 0.1, 0.8, 0.05, 0.7]  # A, C, E should be chosen
    k = 3
    min_w = 0.10
    max_w = 0.50

    weights = repair_and_decode_weights(individual, assets, k, min_w, max_w)

    # Budget check
    assert np.isclose(np.sum(weights), 1.0, atol=1e-5), f"Budget failed: {np.sum(weights)}"

    # Cardinality check
    active_indices = np.where(weights > 1e-5)[0]
    assert len(active_indices) <= k, f"Cardinality exceeded: {len(active_indices)}"

    # Bounds check
    for idx in active_indices:
        w = weights[idx]
        assert w >= min_w - 1e-5, f"Lower bound violated: {w} < {min_w}"
        assert w <= max_w + 1e-5, f"Upper bound violated: {w} > {max_w}"


def test_ga_reproducibility(toy_market):
    """# NFR-01: Two runs with the same seed must produce identical results."""
    cov_df, mean_df, _ = toy_market
    params = OptimizationParams(
        cardinality_limit=3,
        min_weight=0.10,
        max_weight=0.50,
        ga_seed=123,
        ga_pop_size=30,
        ga_generations=15,
    )

    res1 = run_genetic_algorithm(cov_df, mean_df, params)
    res2 = run_genetic_algorithm(cov_df, mean_df, params)

    assert res1.best_objective == res2.best_objective
    assert res1.best_weights == res2.best_weights
    assert res1.selected_assets == res2.selected_assets


def test_ga_execution_and_metrics(toy_market):
    """# FR-03, acceptance criterion (c): Verify GA returns a valid GAResult with history."""
    cov_df, mean_df, _ = toy_market
    params = OptimizationParams(
        cardinality_limit=2,
        min_weight=0.15,
        max_weight=0.60,
        ga_seed=42,
        ga_pop_size=40,
        ga_generations=20,
    )

    res = run_genetic_algorithm(cov_df, mean_df, params)

    assert len(res.best_weights) <= 2
    assert np.isclose(sum(res.best_weights.values()), 1.0, atol=1e-4)
    assert len(res.history) == 20
    assert res.execution_time_sec > 0
