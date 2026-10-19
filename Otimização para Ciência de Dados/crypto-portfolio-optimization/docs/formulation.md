# Mathematical Formulation: Cryptocurrency Portfolio Optimization

**Project:** crypto-portfolio-optimization  
**Requirements Traceability:** `FR-01`, `FR-02`, `FR-03`, `acceptance criterion (a)`, `Course PDF Stage 1`  
**Solvers:** COIN-OR CBC (MILP), Ipopt (NLP), Couenne (MINLP), and DEAP (Genetic Algorithm)

---

## 1. Context and Problem Definition

The problem addressed is the optimal allocation of capital among $N$ liquid cryptocurrency assets. Cryptocurrencies exhibit heavy tails, extreme volatility, and non-linear risk dynamics. We formulate three complementary optimization models reflecting the requirements of the course syllabus:
1. **Model 1 (MILP - CBC):** Minimization of Conditional Value at Risk ($\text{CVaR}_\alpha$) under semi-continuous allocation and cardinality constraints.
2. **Model 2 (NLP - Ipopt):** Continuous Mean-Variance Markowitz optimization.
3. **Model 3 (MINLP - Couenne):** Cardinality-constrained Mean-Variance Markowitz optimization with discrete buy-in thresholds (semi-continuous bounds).

---

## 2. Common Indices, Sets, and Parameters

### Indices and Sets
- $i, j \in I = \{1, 2, \dots, N\}$: Set of candidate cryptocurrency assets ($N = 19$).
- $s \in S = \{1, 2, \dots, T\}$: Set of discrete scenarios (daily historical return observations, $T \ge 1000$).

### Parameters
- $r_{i, s} \in \mathbb{R}$: Daily return of asset $i$ in scenario $s$.
- $p_s = \frac{1}{T}$: Probability of occurrence of scenario $s$.
- $\bar{\mu}_i = \frac{1}{T} \sum_{s=1}^T r_{i,s}$: Historical mean expected return of asset $i$.
- $\boldsymbol{\Sigma} = (\sigma_{ij})_{N \times N}$: Sample covariance matrix of daily returns:
  $$\sigma_{ij} = \frac{1}{T - 1} \sum_{s=1}^T (r_{i,s} - \bar{\mu}_i)(r_{j,s} - \bar{\mu}_j)$$
- $R_{target} \in \mathbb{R}$: Minimum acceptable annualized or daily expected return for the portfolio.
- $\alpha \in (0, 1)$: Confidence level for Value at Risk and CVaR (default $\alpha = 0.95$).
- $K \in \{1, \dots, N\}$: Maximum cardinality (maximum number of active assets, default $K = 5$).
- $w_{min} \in (0, 1)$: Minimum allocation proportion if asset is selected (semi-continuous lower bound, default $w_{min} = 0.05$).
- $w_{max} \in (0, 1)$: Maximum allocation proportion to avoid excessive concentration (default $w_{max} = 0.40$).
- $\lambda \ge 0$: Risk-aversion trade-off parameter.

---

## 3. Model 1: CVaR Minimization (MILP)

Following Rockafellar and Uryasev (2000), Conditional Value at Risk at confidence level $\alpha$ is linearized by introducing an auxiliary threshold variable $\gamma$ (representing the $\text{VaR}_\alpha$) and scenario shortfall variables $u_s$.

### Decision Variables
- $w_i \in [0, w_{max}]$: Weight of asset $i$ in the portfolio (continuous).
- $z_i \in \{0, 1\}$: Binary indicator equal to $1$ if asset $i$ is selected ($w_i > 0$), and $0$ otherwise.
- $\gamma \in \mathbb{R}$: Value at Risk ($\text{VaR}_\alpha$) decision variable (continuous, unconstrained sign).
- $u_s \ge 0$: Portfolio loss in scenario $s$ in excess of $\gamma$ (continuous).

### Mathematical Formulation
$$\min_{w, z, \gamma, u} \quad \text{CVaR}_\alpha(w) = \gamma + \frac{1}{(1 - \alpha) T} \sum_{s=1}^T u_s$$

**Subject to:**

1. **Scenario Shortfall Linking Constraints:**
   $$u_s \ge -\sum_{i=1}^N r_{i,s} w_i - \gamma, \quad \forall s \in S$$
   $$u_s \ge 0, \quad \forall s \in S$$

2. **Target Return Constraint:**
   $$\sum_{i=1}^N \bar{\mu}_i w_i \ge R_{target}$$

3. **Budget (Capital Preservation) Constraint:**
   $$\sum_{i=1}^N w_i = 1$$

4. **Semi-continuous Lower and Upper Bounds:**
   $$w_{min} z_i \le w_i \le w_{max} z_i, \quad \forall i \in I$$

5. **Cardinality Limit Constraint:**
   $$\sum_{i=1}^N z_i \le K$$

6. **Variable Domains:**
   $$w_i \ge 0, \quad z_i \in \{0, 1\}, \quad \forall i \in I$$
   $$\gamma \in \mathbb{R}$$

**Target Solver:** COIN-OR **CBC** (MILP).

---

## 4. Model 2: Continuous Mean-Variance Markowitz (NLP)

The classic Markowitz formulation minimizes total portfolio variance subject to budget and expected return constraints, with continuous weights.

### Decision Variables
- $w_i \in [0, w_{max}]$: Weight of asset $i$ (continuous).

### Mathematical Formulation
$$\min_{w} \quad \frac{1}{2} \sum_{i=1}^N \sum_{j=1}^N w_i \sigma_{ij} w_j - \lambda \sum_{i=1}^N \bar{\mu}_i w_i$$

**Subject to:**

1. **Budget Constraint:**
   $$\sum_{i=1}^N w_i = 1$$

2. **Target Return Constraint:**
   $$\sum_{i=1}^N \bar{\mu}_i w_i \ge R_{target}$$

3. **Continuous Box Bounds:**
   $$0 \le w_i \le w_{max}, \quad \forall i \in I$$

**Target Solver:** COIN-OR **Ipopt** (Interior Point NLP solver).

---

## 5. Model 3: Cardinality-Constrained Mean-Variance (MINLP)

Extends Model 2 by enforcing discrete selection rules: exactly or at most $K$ assets can be active, and any active asset must receive at least $w_{min}$ and at most $w_{max}$.

### Decision Variables
- $w_i \in [0, w_{max}]$: Weight of asset $i$ (continuous).
- $z_i \in \{0, 1\}$: Binary indicator for asset $i$.

### Mathematical Formulation
$$\min_{w, z} \quad \frac{1}{2} \sum_{i=1}^N \sum_{j=1}^N w_i \sigma_{ij} w_j - \lambda \sum_{i=1}^N \bar{\mu}_i w_i$$

**Subject to:**

1. **Budget Constraint:**
   $$\sum_{i=1}^N w_i = 1$$

2. **Target Return Constraint:**
   $$\sum_{i=1}^N \bar{\mu}_i w_i \ge R_{target}$$

3. **Semi-continuous Bounds:**
   $$w_{min} z_i \le w_i \le w_{max} z_i, \quad \forall i \in I$$

4. **Cardinality Limit:**
   $$\sum_{i=1}^N z_i \le K$$

5. **Variable Domains:**
   $$w_i \ge 0, \quad z_i \in \{0, 1\}, \quad \forall i \in I$$

**Target Solver:** COIN-OR **Couenne** (Branch-and-Bound MINLP solver).

---

## 6. Metaheuristic Formulation (Genetic Algorithm via DEAP)

The Genetic Algorithm directly targets the non-convex search space of Model 3 (MINLP).

- **Chromosome Representation:**
  A real-valued chromosome $\mathbf{g} = (g_1, g_2, \dots, g_N) \in [0, 1]^N$.
- **Decoding & Feasibility Repair Operator:**
  1. Select the top $k \le K$ indices with largest $g_i$ values.
  2. Clamp/normalize weights so that:
     $$\sum_{i \in \text{selected}} w_i = 1, \quad w_{min} \le w_i \le w_{max}$$
     Non-selected assets receive $w_j = 0$.
  3. If $\sum \bar{\mu}_i w_i < R_{target}$, apply an exact penalty proportional to the shortfall.
- **Fitness Function:**
  $$f(\mathbf{g}) = \frac{1}{2} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} - \lambda \boldsymbol{\mu}^T \mathbf{w} + P \cdot \max(0, R_{target} - \boldsymbol{\mu}^T \mathbf{w})$$
- **Evolutionary Operators:**
  - Selection: Tournament Selection ($k=3$) with Elitism.
  - Crossover: Simulated Binary Crossover (SBX) or Uniform Blend Crossover ($cxpb = 0.8$).
  - Mutation: Gaussian mutation with adaptive probability ($mutpb = 0.2$).

---

## 7. Traceability Matrix

| Component | Framework / Solver | Mathematical Class |
|---|---|---|
| Model 1 (CVaR) | Pyomo + CBC | MILP (Linear Mixed-Integer) |
| Model 2 (Mean-Variance) | Pyomo + Ipopt | NLP (Convex Nonlinear) |
| Model 3 (Cardinality MV) | Pyomo + Couenne | MINLP (Non-Convex Mixed-Integer Nonlinear) |
| Model 4 (Metaheuristic) | DEAP | Metaheuristic / Genetic Algorithm |
