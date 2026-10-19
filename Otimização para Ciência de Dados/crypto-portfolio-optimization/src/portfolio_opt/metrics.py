"""
# FR-04, acceptance criterion (c)
Performance metrics, risk measures (VaR, CVaR, Sharpe ratio), optimality gap calculation,
and consolidated comparative reporting across optimization methods.
"""

from __future__ import annotations

from typing import Dict, List, Any, Union
import numpy as np
import pandas as pd

from portfolio_opt.solvers import OptimizationResult
from portfolio_opt.ga import GAResult


def compute_portfolio_metrics(
    weights: Dict[str, float],
    returns_matrix: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    alpha: float = 0.95,
    risk_free_rate: float = 0.0,
) -> Dict[str, float]:
    """# FR-04: Calculate standard portfolio statistics, annualized values, and tail risk (VaR, CVaR).

    Note: For cryptocurrency 24/7/365 trading, annualization factor is 365 days.
    """
    assets = list(returns_matrix.columns)
    w_vec = np.array([weights.get(a, 0.0) for a in assets], dtype=float)

    # Daily expected return and variance
    daily_return = float(mean_returns.values @ w_vec)
    daily_variance = float(w_vec @ cov_matrix.values @ w_vec)
    daily_volatility = float(np.sqrt(max(0.0, daily_variance)))

    # Annualized metrics (365 days for crypto)
    annual_return = daily_return * 365.0
    annual_volatility = daily_volatility * np.sqrt(365.0)
    sharpe = (
        (annual_return - risk_free_rate) / annual_volatility
        if annual_volatility > 1e-8
        else 0.0
    )

    # Scenario portfolio returns
    port_scenario_returns = returns_matrix.values @ w_vec
    # Losses are -returns
    losses = -port_scenario_returns

    # Value at Risk at level alpha (e.g. 95th percentile of loss)
    var_alpha = float(np.percentile(losses, alpha * 100))
    
    # Conditional Value at Risk: average of losses exceeding VaR
    tail_losses = losses[losses >= var_alpha]
    cvar_alpha = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_alpha

    return {
        "daily_return": round(daily_return, 6),
        "annual_return": round(annual_return, 4),
        "daily_volatility": round(daily_volatility, 6),
        "annual_volatility": round(annual_volatility, 4),
        "sharpe_ratio": round(sharpe, 4),
        "var_95": round(var_alpha, 6),
        "cvar_95": round(cvar_alpha, 6),
    }


def compute_optimality_gap(
    heuristic_obj: float,
    exact_obj: float,
    epsilon: float = 1e-8,
) -> float:
    """# FR-04, acceptance criterion (c): Relative percentage gap between heuristic and exact optimum.

    Formula:
        Gap (%) = |heuristic_obj - exact_obj| / max(|exact_obj|, epsilon) * 100
    """
    denom = max(abs(exact_obj), epsilon)
    gap = (abs(heuristic_obj - exact_obj) / denom) * 100.0
    return round(float(gap), 4)


def build_comparison_summary(
    results: List[Union[OptimizationResult, GAResult]],
    returns_matrix: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    exact_reference_solver: str = "couenne",
    alpha: float = 0.95,
) -> pd.DataFrame:
    """# FR-04, acceptance criterion (c): Build consolidated comparative dataframe across all solvers and GA."""
    # Find exact reference objective for gap comparison
    ref_obj = None
    for r in results:
        if isinstance(r, OptimizationResult) and r.solver_name.lower() == exact_reference_solver.lower():
            if not np.isnan(r.objective_value):
                ref_obj = r.objective_value
                break

    rows = []
    for r in results:
        if isinstance(r, OptimizationResult):
            method_name = f"Pyomo ({r.solver_name.upper()}) - {r.model_name}"
            weights = r.weights
            obj = r.objective_value
            solve_time = r.solve_time_sec
        elif isinstance(r, GAResult):
            method_name = "Algoritmo Genético (DEAP)"
            weights = r.best_weights
            obj = r.best_objective
            solve_time = r.execution_time_sec
        else:
            continue

        metrics = compute_portfolio_metrics(
            weights, returns_matrix, cov_matrix, mean_returns, alpha=alpha
        )

        # Compute gap if reference exact objective is known
        if ref_obj is not None and not np.isnan(obj):
            gap_str = f"{compute_optimality_gap(obj, ref_obj):.2f}%"
        else:
            gap_str = "Ref / N/A"

        # Format asset allocations
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        allocations_str = ", ".join(f"{k}: {v*100:.1f}%" for k, v in sorted_weights if v > 0.005)

        rows.append({
            "Método / Solver": method_name,
            "Objetivo": round(obj, 6) if not np.isnan(obj) else "N/A",
            "Retorno Diário (%)": f"{metrics['daily_return']*100:.3f}%",
            "Retorno Anual (%)": f"{metrics['annual_return']*100:.1f}%",
            "Volatilidade Anual (%)": f"{metrics['annual_volatility']*100:.1f}%",
            "CVaR 95% Diário (%)": f"{metrics['cvar_95']*100:.2f}%",
            "Sharpe Ratio": metrics["sharpe_ratio"],
            "Nº Ativos": len([w for w in weights.values() if w > 0.005]),
            "Alocação": allocations_str,
            "Tempo (s)": f"{solve_time:.2f}s",
            "Gap vs Ótimo": gap_str,
        })

    return pd.DataFrame(rows)
