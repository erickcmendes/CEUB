"""
# FR-08, Course PDF Stage 5
Comparative analysis: Sensitivity analysis on cardinality and risk aversion,
exploration vs exploitation trade-offs, and computational performance evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np
import pandas as pd

from portfolio_opt.params import OptimizationParams
from portfolio_opt.ga import run_genetic_algorithm, GAResult


@dataclass
class SensitivityAnalysisResult:
    """Consolidates sensitivity runs across varying cardinality and risk aversion."""
    cardinality_table: pd.DataFrame
    risk_aversion_table: pd.DataFrame


def run_cardinality_sensitivity(
    cov_df: pd.DataFrame,
    mean_df: pd.Series,
    k_values: List[int] = [2, 3, 5, 7],
    base_params: OptimizationParams = OptimizationParams(),
) -> pd.DataFrame:
    """# FR-08: Evaluate portfolio risk, return, and solve time as cardinality K varies."""
    records = []
    for k in k_values:
        p = OptimizationParams(
            cardinality_limit=k,
            min_weight=base_params.min_weight,
            max_weight=base_params.max_weight,
            target_daily_return=base_params.target_daily_return,
            ga_seed=base_params.ga_seed,
            ga_pop_size=40,
            ga_generations=25,
        )
        res = run_genetic_algorithm(cov_df, mean_df, p)
        records.append({
            "Cardinalidade (K)": k,
            "Ativos Selecionados": len(res.best_weights),
            "Objetivo": res.best_objective,
            "Retorno Diário (%)": f"{res.portfolio_return * 100:.3f}%",
            "Volatilidade Anual (%)": f"{res.portfolio_volatility * np.sqrt(365) * 100:.2f}%",
            "Tempo de Execução (s)": f"{res.execution_time_sec:.2f}s",
        })
    return pd.DataFrame(records)


def run_risk_aversion_sensitivity(
    cov_df: pd.DataFrame,
    mean_df: pd.Series,
    lambda_values: List[float] = [0.1, 0.5, 1.0, 2.5],
    base_params: OptimizationParams = OptimizationParams(),
) -> pd.DataFrame:
    """# FR-08: Evaluate portfolio trade-offs across conservative to aggressive risk aversion."""
    records = []
    for lam in lambda_values:
        p = OptimizationParams(
            cardinality_limit=base_params.cardinality_limit,
            risk_aversion_lambda=lam,
            min_weight=base_params.min_weight,
            max_weight=base_params.max_weight,
            ga_seed=base_params.ga_seed,
            ga_pop_size=40,
            ga_generations=25,
        )
        res = run_genetic_algorithm(cov_df, mean_df, p)
        records.append({
            "Lambda (Aversão)": lam,
            "Perfil": "Conservador" if lam < 0.5 else ("Moderado" if lam <= 1.0 else "Agressivo"),
            "Objetivo": res.best_objective,
            "Retorno Diário (%)": f"{res.portfolio_return * 100:.3f}%",
            "Volatilidade Anual (%)": f"{res.portfolio_volatility * np.sqrt(365) * 100:.2f}%",
            "Tempo de Execução (s)": f"{res.execution_time_sec:.2f}s",
        })
    return pd.DataFrame(records)


def compute_diversity_metrics(ga_result: GAResult) -> Dict[str, float]:
    """# FR-08: Quantify exploration vs exploitation by analyzing fitness dispersion over generations."""
    if not ga_result.history:
        return {"convergence_rate": 0.0, "final_dispersion": 0.0}

    first_mean = ga_result.history[0]["mean_fit"]
    final_mean = ga_result.history[-1]["mean_fit"]
    final_min = ga_result.history[-1]["min_fit"]

    # Rate of fitness reduction
    conv_rate = (first_mean - final_min) / abs(first_mean) if abs(first_mean) > 1e-6 else 0.0
    # Final population spread
    dispersion = abs(final_mean - final_min)

    return {
        "convergence_rate_pct": round(conv_rate * 100, 2),
        "final_generation_spread": round(dispersion, 6),
    }
