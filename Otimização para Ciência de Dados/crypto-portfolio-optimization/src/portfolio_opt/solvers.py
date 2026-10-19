"""
# FR-02, NFR-01, NFR-02, D-003, T-002
Solvers interface: availability verification, execution timing, status reporting and result formatting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Dict, Any

import pyomo.environ as pyo


@dataclass
class OptimizationResult:
    """Standardized representation of solver results across CBC, Ipopt, Couenne and GA."""
    model_name: str
    solver_name: str
    status: str
    termination_condition: str
    objective_value: float
    weights: Dict[str, float] = field(default_factory=dict)
    solve_time_sec: float = 0.0
    is_optimal: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


def check_solver_available(solver_name: str) -> bool:
    """# NFR-02: Check whether a specified solver executable is installed and accessible to Pyomo."""
    try:
        solver = pyo.SolverFactory(solver_name)
        if solver is None:
            return False
        return bool(solver.available(exception_on_error=False))
    except Exception:
        return False


def solve_pyomo_model(
    model: pyo.ConcreteModel,
    solver_name: str,
    time_limit_sec: int | None = None,
    tee: bool = False
) -> OptimizationResult:
    """# FR-02, NFR-02: Solve a Pyomo model with named solver, timing, and error reporting.

    Raises:
        RuntimeError: With a helpful Portuguese message if solver executable is not found.
    """
    if not check_solver_available(solver_name):
        raise RuntimeError(
            f"O solver '{solver_name}' não está disponível ou não foi encontrado no PATH do sistema. "
            f"No Google Colab, certifique-se de executar a célula inicial de instalação dos binários IDAES/apt-get."
        )

    solver = pyo.SolverFactory(solver_name)
    
    # Configure time limit option depending on solver
    if time_limit_sec is not None:
        if solver_name == "cbc":
            solver.options["sec"] = time_limit_sec
        elif solver_name == "ipopt":
            solver.options["max_cpu_time"] = float(time_limit_sec)
        elif solver_name == "couenne":
            solver.options["time_limit"] = float(time_limit_sec)

    start_t = time.perf_counter()
    res = solver.solve(model, tee=tee)
    elapsed_t = time.perf_counter() - start_t

    term_cond = str(res.solver.termination_condition)
    status_str = str(res.solver.status)
    is_optimal = res.solver.termination_condition == pyo.TerminationCondition.optimal

    # Extract weights if variable 'w' exists in the model
    weights = {}
    if hasattr(model, "w"):
        for key in model.w:
            val = pyo.value(model.w[key])
            if val is not None and abs(val) > 1e-6:
                weights[str(key)] = round(float(val), 6)

    # Extract objective value
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        obj_val = float("nan")

    return OptimizationResult(
        model_name=getattr(model, "name", "Pyomo_Model"),
        solver_name=solver_name,
        status=status_str,
        termination_condition=term_cond,
        objective_value=obj_val,
        weights=weights,
        solve_time_sec=round(elapsed_t, 4),
        is_optimal=is_optimal,
    )
