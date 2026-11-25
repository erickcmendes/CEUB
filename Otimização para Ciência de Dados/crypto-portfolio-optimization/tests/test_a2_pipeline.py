"""
# FR-02, FR-07, FR-08, FR-09: Tests for the A2 additions (stages 4, 5 and 6).
"""

import shutil

import numpy as np
import pandas as pd
import pytest

from portfolio_opt.backtest import (
    PANEL_FEATURES,
    STRATEGIES,
    build_panel_features,
    run_walk_forward_backtest,
    train_and_forecast,
)
from portfolio_opt.evaluation import (
    convergence_table,
    generations_to_gap,
    profile_call,
    run_exploration_grid,
)
from portfolio_opt.ga import run_genetic_algorithm
from portfolio_opt.params import OptimizationParams
from portfolio_opt.solvers import check_solver_available

HAS_COUENNE = shutil.which("couenne") is not None


@pytest.fixture
def returns():
    """Synthetic daily returns: 8 assets, ~2.5 years, fixed seed."""
    rng = np.random.default_rng(0)
    idx = pd.date_range("2021-01-01", periods=900, freq="D")
    assets = ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "DOGE", "AVAX"]
    data = rng.normal(0.001, 0.03, size=(len(idx), len(assets)))
    return pd.DataFrame(data, index=idx, columns=assets)


@pytest.fixture
def fast_params():
    return OptimizationParams(target_daily_return=-1.0, ga_pop_size=20, ga_generations=10)


def test_fr02_solver_check_matches_executable_on_path():
    """# FR-02: Regression: a wrong Pyomo keyword made every solver look unavailable."""
    for name in ["cbc", "ipopt", "couenne"]:
        assert check_solver_available(name) == (shutil.which(name) is not None)


def test_fr07_panel_target_is_future_mean_and_features_are_past(returns):
    """# FR-07: The target is the next-horizon mean; features only use the past."""
    panel = build_panel_features(returns, horizon=5)
    d = returns.index[100]
    expected = returns["BTC"].iloc[101:106].mean()
    assert panel.loc[(d, "BTC"), "target"] == pytest.approx(expected)
    assert panel.loc[(d, "BTC"), "mom_7"] == pytest.approx(returns["BTC"].iloc[94:101].mean())
    assert set(PANEL_FEATURES) <= set(panel.columns)


def test_fr07_forecast_has_no_look_ahead(returns):
    """# FR-07: Changing returns after the rebalance date must not change the forecast."""
    panel = build_panel_features(returns, horizon=30)
    t = returns.index[500]
    before = train_and_forecast(panel, t, horizon=30, train_window=365)
    future = returns.copy()
    future.loc[future.index > t] = 0.5
    after = train_and_forecast(build_panel_features(future, horizon=30), t, horizon=30, train_window=365)
    pd.testing.assert_series_equal(before, after)


def test_fr07_walk_forward_backtest_outputs(returns, fast_params):
    """# FR-07: Every strategy has a wealth path, valid weights and metrics."""
    res = run_walk_forward_backtest(returns, fast_params, horizon=30, train_window=365)
    assert list(res.wealth.columns) == STRATEGIES
    assert res.wealth.notna().all().all()
    for n in STRATEGIES:
        w = res.weights[n]
        assert np.allclose(w.sum(axis=1), 1.0)
        assert (w >= -1e-9).all().all()
    opt_w = res.weights[STRATEGIES[0]]
    assert ((opt_w > 1e-6).sum(axis=1) <= fast_params.cardinality_limit).all()
    assert set(res.forecast_quality.index) == {"Previsão ML (Ridge)", "Média Histórica"}
    assert len(res.performance) == len(STRATEGIES)


def test_fr08_profile_call_measures_time_and_cpu():
    """# FR-08: profile_call returns the result and positive wall and CPU time."""
    def busy():
        return sum(i * i for i in range(300_000))
    out, use = profile_call(busy, trace_alloc=True)
    assert out == sum(i * i for i in range(300_000))
    assert use.wall_s > 0 and use.cpu_s > 0
    assert use.py_alloc_peak_mb >= 0


def test_fr08_ga_logs_diversity_and_feasibility():
    """# FR-08: The GA records diversity per generation and flags infeasible K."""
    assets = ["A", "B", "C", "D", "E"]
    cov = pd.DataFrame(np.eye(5) * 0.0004, index=assets, columns=assets)
    mu = pd.Series(0.001, index=assets)
    p = OptimizationParams(target_daily_return=-1.0, ga_pop_size=20, ga_generations=8)
    res = run_genetic_algorithm(cov, mu, p)
    assert {"gene_std", "unique_supports"} <= set(res.history[0])
    assert res.is_feasible
    # K=2 with w_max=0.4 cannot sum to 1: the repair cannot meet the bounds
    bad = run_genetic_algorithm(cov, mu, OptimizationParams(cardinality_limit=2, target_daily_return=-1.0,
                                                            ga_pop_size=20, ga_generations=5))
    assert not bad.is_feasible


def test_fr08_convergence_and_exploration_grid():
    """# FR-08: Convergence table and the exploration grid have the expected shape."""
    assets = ["A", "B", "C", "D", "E", "F"]
    rng = np.random.default_rng(1)
    m = rng.normal(size=(6, 6))
    cov = pd.DataFrame(m @ m.T * 1e-4 + np.eye(6) * 1e-4, index=assets, columns=assets)
    mu = pd.Series(rng.normal(0.001, 0.0005, 6), index=assets)
    p = OptimizationParams(cardinality_limit=4, target_daily_return=-1.0, ga_pop_size=20, ga_generations=10)
    ga = run_genetic_algorithm(cov, mu, p)
    ref = ga.best_objective * 1.01
    ct = convergence_table(ga, ref)
    assert len(ct) == p.ga_generations and "gap_best_pct" in ct
    # best_objective is rounded to 6 decimals, so allow a tiny threshold
    assert generations_to_gap(ga, ga.best_objective, 0.1) <= p.ga_generations
    grid = run_exploration_grid(cov, mu, p, ref, sigmas=[0.1, 0.5], tournament_sizes=[2, 5], seeds=[0, 1])
    assert len(grid) == 4


@pytest.mark.skipif(not HAS_COUENNE, reason="Couenne not installed")
def test_fr08_fr09_exact_vs_heuristic_and_dashboard(returns, tmp_path):
    """# FR-08, FR-09: Couenne is the reference (gap 0) and the dashboard file is written."""
    from portfolio_opt.data import compute_returns_and_scenarios  # noqa: F401
    from portfolio_opt.dashboard import build_dashboard_html
    from portfolio_opt.evaluation import run_exact_vs_heuristic, run_sensitivity

    r = returns.iloc[:400]
    cov, mu = r.cov(), r.mean()
    p = OptimizationParams(cardinality_limit=3, target_daily_return=-1.0, ga_pop_size=20, ga_generations=10)
    ev = run_exact_vs_heuristic(r, cov, mu, p, seeds=[0, 1], time_limit=30)
    assert ev.resources.loc[0, "Gap vs Ótimo (%)"] == 0.0
    # Relaxation bound, up to Ipopt's convergence tolerance
    assert ev.lower_bound.objective_value <= ev.exact.objective_value + 1e-6 * abs(ev.exact.objective_value) + 1e-7
    sens = run_sensitivity(cov, mu, p, k_values=[3], lambda_values=[1.0], n_values=[5], time_limit=30)
    wf = run_walk_forward_backtest(returns, p, horizon=30, train_window=365)
    grid = run_exploration_grid(cov, mu, p, ev.exact.objective_value, sigmas=[0.2], tournament_sizes=[3], seeds=[0])
    out = build_dashboard_html(wf, ev, grid, sens, tmp_path / "d.html")
    text = out.read_text(encoding="utf-8")
    assert "plotly" in text and "Etapa 4" in text and "Etapa 5" in text
