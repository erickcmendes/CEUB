"""
# FR-03, FR-06, NFR-01, acceptance criterion (c), Course PDF Stage 3
Genetic Algorithm for Cardinality-Constrained Portfolio Optimization using DEAP.

Features:
- Real-valued genome encoding [0, 1]^N.
- Deterministic constraint repair operator enforcing:
    1. Cardinality <= K
    2. Budget sum(w) == 1.0
    3. Semi-continuous box bounds: min_weight <= w_i <= max_weight for active assets, 0 otherwise.
- Soft-penalty for target return constraint.
- Elitism preserving the best solution across generations.
- Fixed seed for strict reproducibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
import time
from typing import Dict, List, Tuple

from deap import base, creator, tools
import numpy as np
import pandas as pd

from portfolio_opt.params import OptimizationParams, DEFAULT_PARAMS


@dataclass
class GAResult:
    """Encapsulates results and diagnostics of the Genetic Algorithm execution."""
    best_weights: Dict[str, float]
    best_objective: float
    portfolio_return: float
    portfolio_variance: float
    portfolio_volatility: float
    history: List[Dict[str, float]] = field(default_factory=list)
    execution_time_sec: float = 0.0
    selected_assets: List[str] = field(default_factory=list)


def repair_and_decode_weights(
    individual: List[float],
    assets: List[str],
    cardinality_limit: int,
    min_weight: float,
    max_weight: float,
) -> np.ndarray:
    """# FR-03: Decode real-valued chromosome into feasible portfolio weights.

    Guarantees:
    - Exactly or at most `cardinality_limit` assets have w_i > 0.
    - Active assets satisfy min_weight <= w_i <= max_weight.
    - Inactive assets have w_i = 0.
    - sum(w_i) == 1.0.
    """
    n = len(individual)
    k = min(cardinality_limit, n)
    arr = np.array(individual, dtype=float)

    # 1. Select top K assets by gene magnitude
    top_indices = np.argsort(arr)[-k:]
    weights = np.zeros(n, dtype=float)

    # If all genes are zero, distribute uniformly among top K
    selected_genes = arr[top_indices]
    if np.sum(selected_genes) <= 1e-8:
        selected_genes = np.ones(k, dtype=float)

    # 2. Iterative projection to satisfy sum(w) = 1 and [min_weight, max_weight]
    w_k = selected_genes / np.sum(selected_genes)
    for _ in range(20):
        # Clip to bounds
        w_k = np.clip(w_k, min_weight, max_weight)
        current_sum = np.sum(w_k)
        if abs(current_sum - 1.0) < 1e-7:
            break
        # Distribute discrepancy proportionally across non-locked elements
        diff = 1.0 - current_sum
        free_mask = (w_k > min_weight + 1e-6) & (w_k < max_weight - 1e-6)
        if not np.any(free_mask):
            # If all are at bounds, normalize directly
            w_k = w_k / current_sum
            break
        w_k[free_mask] += diff * (w_k[free_mask] / np.sum(w_k[free_mask]))

    weights[top_indices] = w_k
    return weights


def evaluate_portfolio(
    individual: List[float],
    assets: List[str],
    cov_matrix: np.ndarray,
    mean_returns: np.ndarray,
    params: OptimizationParams,
) -> Tuple[float]:
    """# FR-03: Evaluate fitness (objective function + constraint penalty)."""
    weights = repair_and_decode_weights(
        individual,
        assets,
        params.cardinality_limit,
        params.min_weight,
        params.max_weight,
    )

    # Variance: 0.5 * w^T Sigma w
    variance = 0.5 * float(weights @ cov_matrix @ weights)
    # Return: mu^T w
    ret = float(mean_returns @ weights)

    # Base objective: variance - lambda * return
    obj = variance - params.risk_aversion_lambda * ret

    # Soft penalty if return is below target
    if ret < params.target_daily_return:
        shortfall = params.target_daily_return - ret
        obj += params.ga_penalty_weight * shortfall

    return (obj,)


def run_genetic_algorithm(
    cov_df: pd.DataFrame,
    mean_df: pd.Series,
    params: OptimizationParams = DEFAULT_PARAMS,
) -> GAResult:
    """# FR-03, NFR-01, acceptance criterion (c): Execute the DEAP Genetic Algorithm.

    Reproducible via fixed random seed.
    """
    random.seed(params.ga_seed)
    np.random.seed(params.ga_seed)

    assets = list(cov_df.columns)
    cov_arr = cov_df.values
    mean_arr = mean_df.values
    n_assets = len(assets)

    # Configure DEAP creators safely (avoid duplicate class creation warning)
    if not hasattr(creator, "FitnessMin_Portfolio"):
        creator.create("FitnessMin_Portfolio", base.Fitness, weights=(-1.0,))
    if not hasattr(creator, "Individual_Portfolio"):
        creator.create(
            "Individual_Portfolio",
            list,
            fitness=creator.FitnessMin_Portfolio,
        )

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, 0.0, 1.0)
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.Individual_Portfolio,
        toolbox.attr_float,
        n=n_assets,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register(
        "evaluate",
        evaluate_portfolio,
        assets=assets,
        cov_matrix=cov_arr,
        mean_returns=mean_arr,
        params=params,
    )
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.2, indpb=0.25)
    toolbox.register("select", tools.selTournament, tournsize=params.ga_tournament_size)

    start_time = time.perf_counter()

    pop = toolbox.population(n=params.ga_pop_size)
    hof = tools.HallOfFame(1)

    # Evaluate initial population
    fitnesses = [toolbox.evaluate(ind) for ind in pop]
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    hof.update(pop)

    stats_history: List[Dict[str, float]] = []

    # Evolution loop
    for gen in range(params.ga_generations):
        # Elitism: retain best individual
        best_clone = toolbox.clone(hof[0])

        # Selection
        offspring = toolbox.select(pop, len(pop) - 1)
        offspring = [toolbox.clone(ind) for ind in offspring]

        # Crossover
        for i in range(0, len(offspring) - 1, 2):
            if random.random() < params.ga_cx_prob:
                toolbox.mate(offspring[i], offspring[i + 1])
                del offspring[i].fitness.values
                del offspring[i + 1].fitness.values

        # Mutation & clamping to [0, 1]
        for ind in offspring:
            if random.random() < params.ga_mut_prob:
                toolbox.mutate(ind)
                del ind.fitness.values
            for j in range(len(ind)):
                ind[j] = max(0.0, min(1.0, ind[j]))

        # Re-evaluate invalid offspring
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        new_fitnesses = [toolbox.evaluate(ind) for ind in invalid_ind]
        for ind, fit in zip(invalid_ind, new_fitnesses):
            ind.fitness.values = fit

        # Form new generation with elite individual
        offspring.append(best_clone)
        pop[:] = offspring
        hof.update(pop)

        # Log generation statistics
        fits = [ind.fitness.values[0] for ind in pop]
        stats_history.append({
            "gen": gen + 1,
            "min_fit": float(np.min(fits)),
            "mean_fit": float(np.mean(fits)),
            "max_fit": float(np.max(fits)),
        })

    elapsed_time = time.perf_counter() - start_time

    # Decode best individual
    best_ind = hof[0]
    best_w_arr = repair_and_decode_weights(
        best_ind,
        assets,
        params.cardinality_limit,
        params.min_weight,
        params.max_weight,
    )

    best_weights_dict = {
        assets[i]: round(float(best_w_arr[i]), 6)
        for i in range(n_assets)
        if best_w_arr[i] > 1e-5
    }

    p_var = float(best_w_arr @ cov_arr @ best_w_arr)
    p_vol = float(np.sqrt(p_var))
    p_ret = float(mean_arr @ best_w_arr)

    return GAResult(
        best_weights=best_weights_dict,
        best_objective=round(best_ind.fitness.values[0], 6),
        portfolio_return=round(p_ret, 6),
        portfolio_variance=round(p_var, 6),
        portfolio_volatility=round(p_vol, 6),
        history=stats_history,
        execution_time_sec=round(elapsed_time, 4),
        selected_assets=list(best_weights_dict.keys()),
    )
