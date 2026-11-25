"""
# FR-08, Course PDF Stage 5
Comparative evaluation of the exact solution (Couenne, with the continuous
relaxation solved by Ipopt as a lower bound) against the metaheuristic (GA):
run time, CPU and RAM, convergence, exploration vs exploitation, sensitivity.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
import threading
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
import psutil

from portfolio_opt.ga import GAResult, run_genetic_algorithm
from portfolio_opt.metrics import compute_optimality_gap
from portfolio_opt.models import (
    build_cardinality_minlp_model,
    build_cvar_milp_model,
    build_mean_variance_nlp_model,
)
from portfolio_opt.params import OptimizationParams
from portfolio_opt.solvers import OptimizationResult, solve_pyomo_model


# --------------------------------------------------------------------------- #
# CPU and RAM measurement
# --------------------------------------------------------------------------- #

@dataclass
class ResourceUsage:
    """# FR-08: Resources used by one call, including external solver processes."""
    wall_s: float
    cpu_s: float               # Python process + child solver processes
    cpu_util_pct: float        # cpu_s / wall_s
    rss_increase_mb: float     # peak RSS of the Python process above its baseline
    solver_peak_rss_mb: float  # peak RSS of child processes (CBC, Ipopt, Couenne)
    py_alloc_peak_mb: float    # peak Python heap allocation (tracemalloc), if traced


def profile_call(
    fn: Callable[..., Any], *args, trace_alloc: bool = False, interval: float = 0.005, **kwargs
) -> Tuple[Any, ResourceUsage]:
    """# FR-08: Run `fn` and measure wall time, CPU time and memory.

    A background thread samples the RSS of this process and of its children
    (the solvers run as separate executables, invisible to Python's allocator).
    `trace_alloc=True` also measures the Python heap with tracemalloc, which
    slows Python code down, so time it in a separate call.
    """
    proc = psutil.Process()
    base_rss = proc.memory_info().rss
    peak = {"self": base_rss, "child": 0}
    child_cpu: Dict[int, float] = {}
    stop = threading.Event()

    def _sample() -> None:
        while not stop.is_set():
            try:
                peak["self"] = max(peak["self"], proc.memory_info().rss)
                for ch in proc.children(recursive=True):
                    try:
                        peak["child"] = max(peak["child"], ch.memory_info().rss)
                        ct = ch.cpu_times()
                        child_cpu[ch.pid] = ct.user + ct.system
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except psutil.Error:
                pass
            stop.wait(interval)

    sampler = threading.Thread(target=_sample, daemon=True)
    cpu0, os0 = proc.cpu_times(), os.times()
    if trace_alloc:
        tracemalloc.start()
    sampler.start()
    t0 = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
    finally:
        wall = time.perf_counter() - t0
        stop.set()
        sampler.join()
        alloc_peak = 0.0
        if trace_alloc:
            alloc_peak = tracemalloc.get_traced_memory()[1] / 2**20
            tracemalloc.stop()
    cpu1, os1 = proc.cpu_times(), os.times()

    cpu_self = (cpu1.user - cpu0.user) + (cpu1.system - cpu0.system)
    # POSIX reports waited children in os.times(); Windows does not, so fall back to sampling
    cpu_children = max(
        (os1.children_user - os0.children_user) + (os1.children_system - os0.children_system),
        sum(child_cpu.values()),
    )
    cpu = cpu_self + cpu_children
    return result, ResourceUsage(
        wall_s=wall,
        cpu_s=cpu,
        cpu_util_pct=100.0 * cpu / wall if wall > 0 else 0.0,
        rss_increase_mb=(peak["self"] - base_rss) / 2**20,
        solver_peak_rss_mb=peak["child"] / 2**20,
        py_alloc_peak_mb=alloc_peak,
    )


# --------------------------------------------------------------------------- #
# Exact vs metaheuristic
# --------------------------------------------------------------------------- #

def _solve(builder, data, mu, params, solver, time_limit):
    return solve_pyomo_model(builder(data, mu, params), solver, time_limit_sec=time_limit)


@dataclass
class ExactVsHeuristicResult:
    """# FR-08: Outputs of the head-to-head comparison."""
    resources: pd.DataFrame            # one row per method: objective, gap, CPU, RAM
    ga_seeds: pd.DataFrame             # one row per GA seed
    ga_runs: Dict[int, GAResult]       # full GA results (histories for convergence)
    exact: OptimizationResult          # Couenne
    lower_bound: OptimizationResult    # Ipopt on the continuous relaxation


def run_exact_vs_heuristic(
    returns_matrix: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams,
    seeds: List[int] = list(range(10)),
    time_limit: int = 120,
) -> ExactVsHeuristicResult:
    """# FR-08: Couenne (exact), Ipopt relaxation (bound), CBC (CVaR model) and
    the GA over several seeds, each with its CPU and RAM profile."""
    rows = []

    def _row(method, obj, ref, usage: ResourceUsage, alloc_mb: float, note: str):
        rows.append({
            "Método": method,
            "Objetivo": obj,
            "Gap vs Ótimo (%)": compute_optimality_gap(obj, ref) if ref is not None else np.nan,
            "Tempo de Parede (s)": usage.wall_s,
            "Tempo de CPU (s)": usage.cpu_s,
            "Uso de CPU (%)": usage.cpu_util_pct,
            "RAM Solver Externo (MB)": usage.solver_peak_rss_mb,
            "RAM Python Δ (MB)": usage.rss_increase_mb,
            "Pico Heap Python (MB)": alloc_mb,
            "Observação": note,
        })

    def _twice(fn, *a):
        # One timed run, one traced run (tracemalloc would distort the timing)
        res, use = profile_call(fn, *a)
        _, use_alloc = profile_call(fn, *a, trace_alloc=True)
        return res, use, use_alloc.py_alloc_peak_mb

    exact, u_ex, a_ex = _twice(_solve, build_cardinality_minlp_model, cov_matrix, mean_returns, params, "couenne", time_limit)
    ref = exact.objective_value
    bound, u_lb, a_lb = _twice(_solve, build_mean_variance_nlp_model, cov_matrix, mean_returns, params, "ipopt", time_limit)
    cvar, u_cv, a_cv = _twice(_solve, build_cvar_milp_model, returns_matrix, mean_returns, params, "cbc", time_limit)

    _row("Couenne (MINLP exato)", ref, ref, u_ex, a_ex, f"status: {exact.termination_condition}")
    _row("Ipopt (relaxação contínua)", bound.objective_value, ref, u_lb, a_lb,
         "limitante inferior: sem cardinalidade nem peso mínimo")

    seed_rows, runs = [], {}
    for s in seeds:
        p = replace(params, ga_seed=s)
        ga, use = profile_call(run_genetic_algorithm, cov_matrix, mean_returns, p)
        runs[s] = ga
        seed_rows.append({
            "Semente": s,
            "Objetivo": ga.best_objective,
            "Gap vs Ótimo (%)": compute_optimality_gap(ga.best_objective, ref),
            "Tempo de Parede (s)": use.wall_s,
            "Tempo de CPU (s)": use.cpu_s,
            "Ativos": ", ".join(sorted(ga.selected_assets)),
            "Mesmos ativos do ótimo": set(ga.selected_assets) == set(exact.weights),
        })
    seeds_df = pd.DataFrame(seed_rows)
    _, u_ga_alloc = profile_call(run_genetic_algorithm, cov_matrix, mean_returns, params, trace_alloc=True)
    best_seed = int(seeds_df.loc[seeds_df["Objetivo"].idxmin(), "Semente"])
    _, u_ga = profile_call(run_genetic_algorithm, cov_matrix, mean_returns, replace(params, ga_seed=best_seed))
    _row(f"Algoritmo Genético (melhor de {len(seeds)} sementes)", float(seeds_df["Objetivo"].min()), ref,
         u_ga, u_ga_alloc.py_alloc_peak_mb,
         f"gap médio {seeds_df['Gap vs Ótimo (%)'].mean():.2f}% ± {seeds_df['Gap vs Ótimo (%)'].std():.2f}")
    _row("CBC (CVaR MILP, outro modelo)", cvar.objective_value, None, u_cv, a_cv,
         "objetivo é CVaR, não comparável com o gap")

    return ExactVsHeuristicResult(pd.DataFrame(rows), seeds_df, runs, exact, bound)


def convergence_table(ga: GAResult, ref_obj: float) -> pd.DataFrame:
    """# FR-08: Per-generation best/mean fitness, gap to the optimum and diversity."""
    df = pd.DataFrame(ga.history)
    df["gap_best_pct"] = [compute_optimality_gap(v, ref_obj) for v in df["min_fit"]]
    return df


def generations_to_gap(ga: GAResult, ref_obj: float, threshold_pct: float) -> float:
    """# FR-08: First generation whose best individual is within `threshold_pct` of the optimum."""
    for h in ga.history:
        if compute_optimality_gap(h["min_fit"], ref_obj) <= threshold_pct:
            return float(h["gen"])
    return float("nan")


# --------------------------------------------------------------------------- #
# Exploration vs exploitation
# --------------------------------------------------------------------------- #

def run_exploration_grid(
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams,
    ref_obj: float,
    sigmas: List[float] = [0.05, 0.20, 0.60],
    tournament_sizes: List[int] = [2, 5, 10],
    seeds: List[int] = list(range(5)),
    gap_threshold_pct: float = 2.0,
) -> pd.DataFrame:
    """# FR-08: Mutation strength (exploration) x tournament size (selection
    pressure, exploitation). For each cell: quality, robustness across seeds,
    speed of convergence and the diversity left in the final population."""
    rows = []
    for sigma in sigmas:
        for tsize in tournament_sizes:
            gaps, gens, gstd, supp = [], [], [], []
            for s in seeds:
                p = replace(params, ga_mut_sigma=sigma, ga_tournament_size=tsize, ga_seed=s)
                ga = run_genetic_algorithm(cov_matrix, mean_returns, p)
                gaps.append(compute_optimality_gap(ga.best_objective, ref_obj))
                gens.append(generations_to_gap(ga, ref_obj, gap_threshold_pct))
                gstd.append(ga.history[-1]["gene_std"])
                supp.append(ga.history[-1]["unique_supports"])
            rows.append({
                "Sigma Mutação": sigma,
                "Tamanho Torneio": tsize,
                "Gap Médio (%)": float(np.mean(gaps)),
                "Gap Desvio (%)": float(np.std(gaps)),
                "Melhor Gap (%)": float(np.min(gaps)),
                f"Sementes com Gap ≤ {gap_threshold_pct:g}% (%)": 100.0 * float(np.mean(np.array(gaps) <= gap_threshold_pct)),
                f"Gerações até {gap_threshold_pct:g}% (média)": float(np.nanmean(gens)) if not np.all(np.isnan(gens)) else np.nan,
                "Diversidade Final (desvio dos genes)": float(np.mean(gstd)),
                "Conjuntos de Ativos Distintos (final)": float(np.mean(supp)),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Sensitivity
# --------------------------------------------------------------------------- #

def _exact_and_ga(cov, mu, p, time_limit) -> Dict[str, Any]:
    ex, u_ex = profile_call(_solve, build_cardinality_minlp_model, cov, mu, p, "couenne", time_limit)
    ga, u_ga = profile_call(run_genetic_algorithm, cov, mu, p)
    w = pd.Series(ex.weights).reindex(cov.columns).fillna(0.0)
    return {
        "Objetivo Couenne": ex.objective_value,
        "Objetivo AG": ga.best_objective,
        # Signed gap vs Couenne's solution: negative means the GA found a better
        # point (possible only when Couenne stopped on its time limit). Only
        # meaningful when both solutions are feasible.
        "Gap AG (%)": ((ga.best_objective - ex.objective_value) / max(abs(ex.objective_value), 1e-8) * 100.0
                       if ga.is_feasible and ex.termination_condition != "infeasible" else np.nan),
        "Couenne Provou Ótimo": ex.is_optimal,
        "AG Factível": ga.is_feasible,
        "Tempo Couenne (s)": u_ex.wall_s,
        "Tempo AG (s)": u_ga.wall_s,
        "Status Couenne": ex.termination_condition,
        "Retorno Anual Ótimo": float(mu @ w) * 365.0,
        "Volatilidade Anual Ótima": float(np.sqrt(w @ cov.values @ w) * np.sqrt(365.0)),
        "Ativos Ótimos": ", ".join(sorted(ex.weights)),
    }


def run_sensitivity(
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams,
    k_values: List[int] = [2, 3, 4, 5, 7, 10],
    lambda_values: List[float] = [0.25, 0.5, 1.0, 2.0, 4.0],
    n_values: List[int] = [5, 10, 15, 19],
    time_limit: int = 60,
) -> Dict[str, pd.DataFrame]:
    """# FR-08: Sensitivity of the optimum, of the GA gap and of the run times to
    the cardinality K, the risk aversion lambda and the number of assets N."""
    k_rows = [{"K": k, **_exact_and_ga(cov_matrix, mean_returns, replace(params, cardinality_limit=k), time_limit)}
              for k in k_values]
    l_rows = [{"Lambda": lam, **_exact_and_ga(cov_matrix, mean_returns, replace(params, risk_aversion_lambda=lam), time_limit)}
              for lam in lambda_values]
    # N: fixed, reproducible order (largest mean return first), so that every
    # subset can still meet the target return and stays feasible
    order = mean_returns.sort_values(ascending=False).index
    n_rows = []
    for n in n_values:
        sub = list(order[:n])
        n_rows.append({"N": n, **_exact_and_ga(cov_matrix.loc[sub, sub], mean_returns[sub], params, time_limit)})
    return {
        "cardinalidade": pd.DataFrame(k_rows),
        "aversao_risco": pd.DataFrame(l_rows),
        "num_ativos": pd.DataFrame(n_rows),
    }
