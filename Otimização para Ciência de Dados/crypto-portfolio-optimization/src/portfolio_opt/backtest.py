"""
# FR-07, Course PDF Stage 4
Walk-forward pipeline where the ML forecast feeds the optimizer.

At every rebalance date t the pipeline only uses data available at the close of t:
1. a pooled Ridge model is trained on targets already realized at t;
2. it forecasts the mean daily return of each asset over the next `horizon` days;
3. the forecast (or the historical mean, the A1 approach) feeds the cardinality
   optimizer, and the portfolio is held until the next rebalance date.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from portfolio_opt.params import OptimizationParams

PANEL_FEATURES = ["mom_7", "mom_30", "mom_90", "vol_30", "vol_90", "rel_mom_30", "rank_mom_30"]

STRATEGY_ML = "Otimizador + ML (Ridge)"
STRATEGY_HIST = "Otimizador + Média Histórica"
STRATEGY_MINVAR = "Otimizador Mínima Variância (μ=0)"
STRATEGY_EW = "Igual Peso 1/N"
STRATEGY_BTC = "BTC Buy & Hold"
STRATEGIES = [STRATEGY_ML, STRATEGY_HIST, STRATEGY_MINVAR, STRATEGY_EW, STRATEGY_BTC]

Optimizer = Callable[[pd.DataFrame, pd.Series, OptimizationParams], Dict[str, float]]


def build_panel_features(returns_matrix: pd.DataFrame, horizon: int = 30) -> pd.DataFrame:
    """# FR-07: Long (date, asset) table of features known at the close of `date`,
    plus the target: the mean daily return over (date, date + horizon]."""
    r = returns_matrix
    mom_30 = r.rolling(30).mean()
    blocks = {
        "mom_7": r.rolling(7).mean(),
        "mom_30": mom_30,
        "mom_90": r.rolling(90).mean(),
        "vol_30": r.rolling(30).std(),
        "vol_90": r.rolling(90).std(),
        # Cross-sectional features: how the asset compares with the others today
        "rel_mom_30": mom_30.sub(mom_30.mean(axis=1), axis=0),
        "rank_mom_30": mom_30.rank(axis=1, pct=True),
        # Target only; never used as a feature
        "target": r.rolling(horizon).mean().shift(-horizon),
    }
    panel = pd.concat({k: v.stack(future_stack=True) for k, v in blocks.items()}, axis=1)
    panel.index.names = ["date", "asset"]
    return panel


def train_and_forecast(
    panel: pd.DataFrame,
    as_of: pd.Timestamp,
    horizon: int = 30,
    train_window: int = 365,
    alpha: float = 10.0,
) -> pd.Series:
    """# FR-07: Fit a pooled Ridge on targets already realized at `as_of`, then
    forecast the next-horizon mean daily return of every asset."""
    dates = panel.index.get_level_values("date")
    # A training row dated d has a target ending at d + horizon <= as_of: no look-ahead
    last_train = as_of - pd.Timedelta(days=horizon)
    first_train = as_of - pd.Timedelta(days=train_window)
    train = panel[(dates > first_train) & (dates <= last_train)].dropna()
    today = panel.xs(as_of, level="date")[PANEL_FEATURES].dropna()

    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(train[PANEL_FEATURES], train["target"])
    pred = pd.Series(model.predict(today), index=today.index)
    # Failure guard (ai-features §4): clip to the range of targets seen in training
    lo, hi = train["target"].quantile([0.01, 0.99])
    return pred.clip(lo, hi)


@dataclass
class WalkForwardResult:
    """# FR-07: What the notebook and the dashboard show for Stage 4."""
    wealth: pd.DataFrame                  # daily cumulative wealth per strategy
    daily_returns: pd.DataFrame           # daily net returns per strategy
    weights: Dict[str, pd.DataFrame]      # rebalance date x asset, per strategy
    performance: pd.DataFrame             # out-of-sample financial metrics
    forecast_quality: pd.DataFrame        # predictive metrics: ML vs historical mean
    forecasts: pd.DataFrame               # per (date, asset): ml, hist, realized
    monthly_ic: pd.DataFrame              # Spearman IC per rebalance date
    rebalance_dates: List[pd.Timestamp] = field(default_factory=list)


def _performance_row(daily: pd.Series, turnover: float) -> Dict[str, float]:
    wealth = (1.0 + daily).cumprod()
    ann_vol = float(daily.std() * np.sqrt(365.0))
    losses = -daily.values
    var95 = np.percentile(losses, 95)
    return {
        "Retorno Anual (CAGR)": float(wealth.iloc[-1] ** (365.0 / len(daily)) - 1.0),
        "Volatilidade Anual": ann_vol,
        "Sharpe": float(daily.mean() * 365.0 / ann_vol) if ann_vol > 0 else 0.0,
        "Máx. Drawdown": float((wealth / wealth.cummax() - 1.0).min()),
        "CVaR 95% Diário": float(losses[losses >= var95].mean()),
        "Giro Médio por Rebalanceamento": turnover,
        "Riqueza Final (R$1 inicial)": float(wealth.iloc[-1]),
    }


def _ga_optimizer(cov_df: pd.DataFrame, mu: pd.Series, p: OptimizationParams) -> Dict[str, float]:
    from portfolio_opt.ga import run_genetic_algorithm
    return run_genetic_algorithm(cov_df, mu, p).best_weights


def run_walk_forward_backtest(
    returns_matrix: pd.DataFrame,
    params: OptimizationParams,
    horizon: int = 30,
    train_window: int = 365,
    cost_rate: float = 0.001,
    ridge_alpha: float = 10.0,
    optimizer: Optimizer | None = None,
) -> WalkForwardResult:
    """# FR-07, Course PDF Stage 4: Out-of-sample walk-forward validation.

    Strategies: optimizer fed by the ML forecast, optimizer fed by the historical
    mean (A1), the same optimizer with no return estimate (minimum variance,
    a control), equal weight 1/N and BTC buy-and-hold. Rebalance every `horizon`
    days with a proportional cost `cost_rate` on turnover. Between rebalances the
    weights drift with prices (buy-and-hold inside the period).
    """
    optimizer = optimizer or _ga_optimizer
    assets = list(returns_matrix.columns)
    panel = build_panel_features(returns_matrix, horizon)
    idx = returns_matrix.index
    start = idx[0] + pd.Timedelta(days=train_window)
    rebal = [d for d in idx[idx >= start][::horizon] if d < idx[-1]]

    w_hist: Dict[str, list] = {n: [] for n in STRATEGIES}
    daily: Dict[str, list] = {n: [] for n in STRATEGIES}
    turn: Dict[str, list] = {n: [] for n in STRATEGIES}
    prev = {n: pd.Series(0.0, index=assets) for n in STRATEGIES}
    fc_rows = []

    for j, t in enumerate(rebal):
        window = returns_matrix.loc[(idx > t - pd.Timedelta(days=train_window)) & (idx <= t)]
        cov = window.cov()
        mu_hist = window.mean()
        mu_ml = train_and_forecast(panel, t, horizon, train_window, ridge_alpha)
        mu_ml = mu_ml.reindex(assets).fillna(mu_hist)

        targets = {
            STRATEGY_ML: pd.Series(optimizer(cov, mu_ml, params)),
            STRATEGY_HIST: pd.Series(optimizer(cov, mu_hist, params)),
            # Control: same optimizer and covariance, no return estimate at all
            STRATEGY_MINVAR: pd.Series(optimizer(cov, mu_hist * 0.0, params)),
            STRATEGY_EW: pd.Series(1.0 / len(assets), index=assets),
            STRATEGY_BTC: pd.Series({"BTC": 1.0}),
        }

        t_end = rebal[j + 1] if j + 1 < len(rebal) else idx[-1]
        hold = returns_matrix.loc[(idx > t) & (idx <= t_end)]
        realized = returns_matrix.loc[(idx > t) & (idx <= t + pd.Timedelta(days=horizon))].mean()
        for a in assets:
            fc_rows.append({"date": t, "asset": a, "ml": mu_ml[a], "hist": mu_hist[a], "realized": realized[a]})

        growth = (1.0 + hold).cumprod()
        for n in STRATEGIES:
            w = targets[n].reindex(assets).fillna(0.0)
            w = w / w.sum()
            tw = float((w - prev[n]).abs().sum())
            turn[n].append(tw)
            w_hist[n].append(w.rename(t))
            value = (growth * w).sum(axis=1)
            r = value.pct_change()
            r.iloc[0] = value.iloc[0] - 1.0 - cost_rate * tw
            daily[n].append(r)
            drifted = growth.iloc[-1] * w
            prev[n] = drifted / drifted.sum()

    daily_df = pd.DataFrame({n: pd.concat(daily[n]) for n in STRATEGIES})
    perf = pd.DataFrame(
        {n: _performance_row(daily_df[n], float(np.mean(turn[n]))) for n in STRATEGIES}
    ).T

    fc = pd.DataFrame(fc_rows)
    quality, ic_cols = {}, {}
    for col, label in [("ml", "Previsão ML (Ridge)"), ("hist", "Média Histórica")]:
        err = fc[col] - fc["realized"]
        ic = fc.groupby("date")[[col, "realized"]].apply(
            lambda g: g[col].corr(g["realized"], method="spearman")
        )
        ic_cols[label] = ic
        quality[label] = {
            "RMSE (ret. diário médio)": float(np.sqrt((err ** 2).mean())),
            "MAE (ret. diário médio)": float(err.abs().mean()),
            "Acerto de Direção (%)": float((np.sign(fc[col]) == np.sign(fc["realized"])).mean() * 100),
            "IC de Spearman médio": float(ic.mean()),
            "Meses com IC > 0 (%)": float((ic > 0).mean() * 100),
        }

    return WalkForwardResult(
        wealth=(1.0 + daily_df).cumprod(),
        daily_returns=daily_df,
        weights={n: pd.DataFrame(w_hist[n]) for n in STRATEGIES},
        performance=perf,
        forecast_quality=pd.DataFrame(quality).T,
        forecasts=fc,
        monthly_ic=pd.DataFrame(ic_cols),
        rebalance_dates=rebal,
    )
