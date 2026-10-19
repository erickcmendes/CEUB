"""
# FR-01, FR-02, acceptance criterion (a), acceptance criterion (b)
Mathematical models in Pyomo:
- Model 1: CVaR Minimization (MILP) -> Solved by CBC
- Model 2: Continuous Mean-Variance Markowitz (NLP) -> Solved by Ipopt
- Model 3: Cardinality-Constrained Mean-Variance (MINLP) -> Solved by Couenne
"""

from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo

from portfolio_opt.params import OptimizationParams, DEFAULT_PARAMS


def build_cvar_milp_model(
    returns_scenarios: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams = DEFAULT_PARAMS,
    name: str = "CVaR_MILP_CBC"
) -> pyo.ConcreteModel:
    """# FR-01, FR-02: Mixed-Integer Linear Program minimizing CVaR.

    Linearized via Rockafellar & Uryasev auxiliary variables (gamma, u_s).
    """
    assets = list(returns_scenarios.columns)
    scenarios = list(range(len(returns_scenarios)))
    t_count = len(scenarios)
    alpha = params.cvar_alpha

    m = pyo.ConcreteModel(name=name)

    # Sets
    m.I = pyo.Set(initialize=assets)
    m.S = pyo.Set(initialize=scenarios)

    # Variables
    m.w = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=(0.0, params.max_weight))
    m.z = pyo.Var(m.I, domain=pyo.Binary)
    m.gamma = pyo.Var(domain=pyo.Reals, initialize=0.0)
    m.u = pyo.Var(m.S, domain=pyo.NonNegativeReals, initialize=0.0)

    # Objective: Minimize gamma + 1/((1 - alpha)*T) * sum(u_s)
    scaling = 1.0 / ((1.0 - alpha) * t_count)
    m.obj = pyo.Objective(
        expr=m.gamma + scaling * sum(m.u[s] for s in m.S),
        sense=pyo.minimize
    )

    # Scenario loss constraint: u_s >= -sum(r_is * w_i) - gamma
    # Pre-extract scenario values as a 2D numpy array for fast Pyomo rule generation
    ret_values = returns_scenarios.values  # shape: (T, N)
    asset_idx_map = {asset: idx for idx, asset in enumerate(assets)}

    def scenario_rule(model, s):
        port_return = sum(float(ret_values[s, asset_idx_map[i]]) * model.w[i] for i in model.I)
        return model.u[s] >= -port_return - model.gamma
    m.c_scenario = pyo.Constraint(m.S, rule=scenario_rule)

    # Budget constraint: sum(w_i) == 1
    m.c_budget = pyo.Constraint(expr=sum(m.w[i] for i in m.I) == 1.0)

    # Target return constraint
    m.c_target_return = pyo.Constraint(
        expr=sum(float(mean_returns[i]) * m.w[i] for i in m.I) >= params.target_daily_return
    )

    # Semi-continuous bounds: min_weight * z_i <= w_i <= max_weight * z_i
    def lower_bound_rule(model, i):
        return model.w[i] >= params.min_weight * model.z[i]
    m.c_lb = pyo.Constraint(m.I, rule=lower_bound_rule)

    def upper_bound_rule(model, i):
        return model.w[i] <= params.max_weight * model.z[i]
    m.c_ub = pyo.Constraint(m.I, rule=upper_bound_rule)

    # Cardinality constraint: sum(z_i) <= K
    m.c_cardinality = pyo.Constraint(
        expr=sum(m.z[i] for i in m.I) <= params.cardinality_limit
    )

    return m


def build_mean_variance_nlp_model(
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams = DEFAULT_PARAMS,
    name: str = "Mean_Variance_NLP_Ipopt"
) -> pyo.ConcreteModel:
    """# FR-01, FR-02: Continuous Markowitz Mean-Variance NLP for Ipopt."""
    assets = list(cov_matrix.columns)
    m = pyo.ConcreteModel(name=name)

    m.I = pyo.Set(initialize=assets)
    init_w = 1.0 / len(assets)
    m.w = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=(0.0, params.max_weight), initialize=init_w)

    # Pre-extract covariance matrix
    cov_dict = cov_matrix.to_dict()

    # Objective: 0.5 * w^T Sigma w - lambda * mu^T w
    var_expr = 0.5 * sum(
        m.w[i] * float(cov_dict[i][j]) * m.w[j]
        for i in m.I for j in m.I
    )
    ret_expr = params.risk_aversion_lambda * sum(
        float(mean_returns[i]) * m.w[i] for i in m.I
    )
    m.obj = pyo.Objective(expr=var_expr - ret_expr, sense=pyo.minimize)

    # Budget constraint
    m.c_budget = pyo.Constraint(expr=sum(m.w[i] for i in m.I) == 1.0)

    # Target return constraint
    m.c_target_return = pyo.Constraint(
        expr=sum(float(mean_returns[i]) * m.w[i] for i in m.I) >= params.target_daily_return
    )

    return m


def build_cardinality_minlp_model(
    cov_matrix: pd.DataFrame,
    mean_returns: pd.Series,
    params: OptimizationParams = DEFAULT_PARAMS,
    name: str = "Cardinality_MINLP_Couenne"
) -> pyo.ConcreteModel:
    """# FR-01, FR-02: Cardinality-Constrained Mean-Variance MINLP for Couenne."""
    assets = list(cov_matrix.columns)
    k_limit = min(params.cardinality_limit, len(assets))
    
    m = pyo.ConcreteModel(name=name)
    m.I = pyo.Set(initialize=assets)

    init_w = 1.0 / k_limit
    m.w = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=(0.0, params.max_weight), initialize=0.0)
    m.z = pyo.Var(m.I, domain=pyo.Binary, initialize=0)

    # Initialize first K assets
    for idx, asset in enumerate(assets):
        if idx < k_limit:
            m.w[asset].set_value(init_w)
            m.z[asset].set_value(1)

    cov_dict = cov_matrix.to_dict()

    # Objective: 0.5 * w^T Sigma w - lambda * mu^T w
    var_expr = 0.5 * sum(
        m.w[i] * float(cov_dict[i][j]) * m.w[j]
        for i in m.I for j in m.I
    )
    ret_expr = params.risk_aversion_lambda * sum(
        float(mean_returns[i]) * m.w[i] for i in m.I
    )
    m.obj = pyo.Objective(expr=var_expr - ret_expr, sense=pyo.minimize)

    # Budget constraint
    m.c_budget = pyo.Constraint(expr=sum(m.w[i] for i in m.I) == 1.0)

    # Target return constraint
    m.c_target_return = pyo.Constraint(
        expr=sum(float(mean_returns[i]) * m.w[i] for i in m.I) >= params.target_daily_return
    )

    # Semi-continuous bounds
    def lower_bound_rule(model, i):
        return model.w[i] >= params.min_weight * model.z[i]
    m.c_lb = pyo.Constraint(m.I, rule=lower_bound_rule)

    def upper_bound_rule(model, i):
        return model.w[i] <= params.max_weight * model.z[i]
    m.c_ub = pyo.Constraint(m.I, rule=upper_bound_rule)

    # Cardinality constraint
    m.c_cardinality = pyo.Constraint(
        expr=sum(m.z[i] for i in m.I) <= params.cardinality_limit
    )

    return m
