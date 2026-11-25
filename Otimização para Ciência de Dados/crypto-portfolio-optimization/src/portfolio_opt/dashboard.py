"""
# FR-09, Course PDF Stage 6
Interactive dashboard (Plotly) for the metrics and goals of the project:
the same figures are shown inline in the notebook and exported to one
self-contained HTML file for the presentation.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go

from portfolio_opt.backtest import STRATEGIES, WalkForwardResult
from portfolio_opt.evaluation import ExactVsHeuristicResult, convergence_table

# Validated categorical palette (fixed order, colour follows the entity)
LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"]
SEQ_BLUE = [[0.0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"], [0.75, "#1c5cab"], [1.0, "#0d366b"]]
STRATEGY_COLOR = dict(zip(STRATEGIES, LIGHT))
METHOD_COLOR = {"Couenne": LIGHT[0], "Ipopt": LIGHT[1], "AG": LIGHT[2], "CBC": LIGHT[3]}

INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
FONT = "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"


def _base(fig: go.Figure, title: str, y_title: str = "", x_title: str = "", height: int = 360) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=15, color=INK)),
        font=dict(family=FONT, size=12, color=INK2),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        height=height, margin=dict(l=56, r=24, t=56, b=48),
        hovermode="x unified" if fig.data and fig.data[0].type == "scatter" else "closest",
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(color=INK2)),
        hoverlabel=dict(bgcolor="#ffffff", font=dict(color=INK)),
    )
    fig.update_xaxes(title=x_title, gridcolor=GRID, linecolor=GRID, zeroline=False)
    fig.update_yaxes(title=y_title, gridcolor=GRID, linecolor=GRID, zerolinecolor="#c9c8c2")
    return fig


def _method_color(name: str) -> str:
    for key, color in METHOD_COLOR.items():
        if name.startswith(key) or (key == "AG" and name.startswith("Algoritmo")):
            return color
    return LIGHT[4]


# --------------------------------------------------------------------------- #
# Stage 4 figures
# --------------------------------------------------------------------------- #

def fig_wealth(wf: WalkForwardResult) -> go.Figure:
    """# FR-09: Out-of-sample cumulative wealth, one line per strategy, labelled at the end."""
    fig = go.Figure()
    for n in STRATEGIES:
        s = wf.wealth[n]
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=n, mode="lines",
                                 line=dict(color=STRATEGY_COLOR[n], width=2),
                                 hovertemplate="%{y:.2f}"))
        fig.add_annotation(x=s.index[-1], y=np.log10(s.iloc[-1]), text=f"{s.iloc[-1]:.2f}",
                           showarrow=False, xanchor="left", xshift=4, font=dict(color=INK2, size=11))
    fig.update_yaxes(type="log")
    return _base(fig, "Riqueza acumulada fora da amostra (R$ 1 investido em jan/2022)", "Riqueza (escala log)")


def fig_drawdown(wf: WalkForwardResult) -> go.Figure:
    """# FR-09: Drawdown from the running peak, per strategy."""
    fig = go.Figure()
    for n in STRATEGIES:
        w = wf.wealth[n]
        dd = (w / w.cummax() - 1.0) * 100
        fig.add_trace(go.Scatter(x=dd.index, y=dd.values, name=n, mode="lines",
                                 line=dict(color=STRATEGY_COLOR[n], width=2),
                                 hovertemplate="%{y:.1f}%"))
    return _base(fig, "Drawdown: queda a partir do pico anterior", "Drawdown (%)")


def fig_allocation(wf: WalkForwardResult, strategy: str) -> go.Figure:
    """# FR-09: Weights chosen at each rebalance (asset x date heatmap)."""
    w = wf.weights[strategy]
    w = w.loc[:, w.sum() > 0] * 100
    fig = go.Figure(go.Heatmap(
        z=w.T.values, x=[d.strftime("%Y-%m") for d in w.index], y=list(w.columns),
        colorscale=[[0.0, "rgba(0,0,0,0)"], [0.001, SEQ_BLUE[0][1]]] + SEQ_BLUE[1:],
        zmin=0, zmax=40, xgap=2, ygap=2,
        colorbar=dict(title="Peso (%)", thickness=12),
        hovertemplate="%{y} em %{x}: %{z:.1f}%<extra></extra>",
    ))
    return _base(fig, f"Alocação ao longo do tempo: {strategy}", height=420)


def fig_monthly_ic(wf: WalkForwardResult) -> go.Figure:
    """# FR-09: Spearman IC of each forecast per rebalance date (predictive power)."""
    fig = go.Figure()
    for i, col in enumerate(wf.monthly_ic.columns):
        s = wf.monthly_ic[col]
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=f"{col} (média {s.mean():+.3f})",
                                 mode="lines+markers", line=dict(color=LIGHT[i], width=2),
                                 marker=dict(size=8), hovertemplate="%{y:+.2f}"))
    fig.add_hline(y=0, line=dict(color="#8a8984", width=1))
    return _base(fig, "Poder preditivo: correlação de postos (IC) entre previsão e retorno realizado",
                 "IC de Spearman")


# --------------------------------------------------------------------------- #
# Stage 5 figures
# --------------------------------------------------------------------------- #

def fig_convergence_gap(ev: ExactVsHeuristicResult) -> go.Figure:
    """# FR-09: Best-individual gap to the Couenne optimum per generation, per seed."""
    ref = ev.exact.objective_value
    fig = go.Figure()
    for s, ga in ev.ga_runs.items():
        ct = convergence_table(ga, ref)
        fig.add_trace(go.Scatter(x=ct["gen"], y=ct["gap_best_pct"], mode="lines",
                                 name=f"semente {s}", showlegend=False,
                                 line=dict(color="#b5b4ae", width=1),
                                 hovertemplate=f"semente {s}: " + "%{y:.2f}%<extra></extra>"))
    med = pd.concat([convergence_table(g, ref).set_index("gen")["gap_best_pct"] for g in ev.ga_runs.values()], axis=1).median(axis=1)
    fig.add_trace(go.Scatter(x=med.index, y=med.values, mode="lines", name="Mediana das sementes",
                             line=dict(color=LIGHT[0], width=2.5), hovertemplate="mediana: %{y:.2f}%<extra></extra>"))
    fig.update_yaxes(type="log")
    fig = _base(fig, "Convergência do AG: gap do melhor indivíduo até o ótimo exato", "Gap vs Couenne (%, log)", "Geração")
    fig.update_layout(hovermode="closest")
    return fig


def fig_convergence_diversity(ev: ExactVsHeuristicResult) -> go.Figure:
    """# FR-09: Population diversity per generation (exploration fading into exploitation)."""
    med = pd.concat([pd.DataFrame(g.history).set_index("gen")["unique_supports"] for g in ev.ga_runs.values()], axis=1).median(axis=1)
    fig = go.Figure(go.Scatter(x=med.index, y=med.values, mode="lines", name="Conjuntos distintos",
                               line=dict(color=LIGHT[1], width=2), hovertemplate="%{y:.0f} conjuntos"))
    return _base(fig, "Diversidade: conjuntos de ativos distintos na população (mediana)", "Conjuntos de K ativos", "Geração")


def fig_exploration_grid(grid: pd.DataFrame) -> go.Figure:
    """# FR-09: Mean gap per (mutation sigma, tournament size) cell."""
    piv = grid.pivot(index="Sigma Mutação", columns="Tamanho Torneio", values="Gap Médio (%)")
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"torneio {c}" for c in piv.columns], y=[f"σ = {i}" for i in piv.index],
        colorscale=SEQ_BLUE, xgap=2, ygap=2, text=np.round(piv.values, 2), texttemplate="%{text}%",
        colorbar=dict(title="Gap médio (%)", thickness=12),
        hovertemplate="%{y}, %{x}: gap médio %{z:.2f}%<extra></extra>",
    ))
    return _base(fig, "Exploração (σ da mutação) x explotação (pressão de seleção)", height=340)


def fig_resources(ev: ExactVsHeuristicResult, column: str, title: str, unit: str) -> go.Figure:
    """# FR-09: One resource measure per method (time, CPU or RAM)."""
    r = ev.resources
    fig = go.Figure(go.Bar(
        y=r["Método"], x=r[column], orientation="h",
        marker=dict(color=[_method_color(m) for m in r["Método"]], cornerradius=4),
        text=[f"{v:.2f} {unit}" for v in r[column]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.2f} " + unit + "<extra></extra>",
    ))
    fig = _base(fig, title, "", unit, height=300)
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_layout(margin=dict(r=72))
    return fig


def fig_sensitivity_times(table: pd.DataFrame, key: str, title: str) -> go.Figure:
    """# FR-09: Couenne vs GA run time as one parameter changes (grouped bars)."""
    x = [str(v) for v in table[key]]
    fig = go.Figure([
        go.Bar(x=x, y=table["Tempo Couenne (s)"], name="Couenne (exato)", marker=dict(color=LIGHT[0], cornerradius=4)),
        go.Bar(x=x, y=table["Tempo AG (s)"], name="Algoritmo Genético", marker=dict(color=LIGHT[2], cornerradius=4)),
    ])
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.06)
    fig.update_traces(hovertemplate="%{y:.2f} s")
    return _base(fig, title, "Tempo de parede (s)", key, height=340)


def fig_sensitivity_gap(sens: Dict[str, pd.DataFrame]) -> go.Figure:
    """# FR-09: GA gap to the optimum along each sensitivity axis (small multiples)."""
    from plotly.subplots import make_subplots
    keys = [("cardinalidade", "K"), ("aversao_risco", "Lambda"), ("num_ativos", "N")]
    fig = make_subplots(rows=1, cols=3, subplot_titles=["Cardinalidade K", "Aversão ao risco λ", "Número de ativos N"],
                        horizontal_spacing=0.08)
    for i, (k, col) in enumerate(keys, start=1):
        t = sens[k]
        fig.add_trace(go.Bar(x=[str(v) for v in t[col]], y=t["Gap AG (%)"].fillna(0), showlegend=False,
                             marker=dict(color=[LIGHT[0] if f else "#b5b4ae" for f in t["AG Factível"]], cornerradius=4),
                             text=[("inviável" if not f else f"{g:.1f}%") for g, f in zip(t["Gap AG (%)"], t["AG Factível"])],
                             textposition="outside", hovertemplate="%{x}: %{text}<extra></extra>"), row=1, col=i)
    fig = _base(fig, "Gap do AG à solução do Couenne (cinza = AG violou as restrições; negativo = AG melhor que um Couenne interrompido)", "Gap (%)", height=340)
    fig.update_annotations(font=dict(color=INK2, size=12))
    return fig


def fig_frontier(sens: Dict[str, pd.DataFrame]) -> go.Figure:
    """# FR-09: Exact optima as lambda varies: the risk-return trade-off."""
    t = sens["aversao_risco"]
    fig = go.Figure(go.Scatter(
        x=t["Volatilidade Anual Ótima"] * 100, y=t["Retorno Anual Ótimo"] * 100, mode="lines+markers+text",
        text=[f"λ={v:g}" for v in t["Lambda"]], textposition="top left", textfont=dict(color=INK2),
        line=dict(color=LIGHT[0], width=2), marker=dict(size=10, line=dict(color=SURFACE, width=2)),
        hovertemplate="vol %{x:.1f}% · retorno %{y:.1f}%<extra></extra>", name="Ótimo Couenne",
    ))
    fig = _base(fig, "Fronteira risco-retorno das carteiras ótimas (K fixo)", "Retorno anual esperado (%)", "Volatilidade anual (%)")
    fig.update_layout(hovermode="closest")
    return fig


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def build_figures(wf: WalkForwardResult, ev: ExactVsHeuristicResult, grid: pd.DataFrame,
                  sens: Dict[str, pd.DataFrame]) -> Dict[str, go.Figure]:
    """# FR-09: Every dashboard figure, keyed by a stable name."""
    return {
        "wealth": fig_wealth(wf),
        "drawdown": fig_drawdown(wf),
        "ic": fig_monthly_ic(wf),
        "allocation": fig_allocation(wf, STRATEGIES[0]),
        "conv_gap": fig_convergence_gap(ev),
        "conv_div": fig_convergence_diversity(ev),
        "grid": fig_exploration_grid(grid),
        "time": fig_resources(ev, "Tempo de Parede (s)", "Tempo de parede por método", "s"),
        "ram": fig_resources(ev, "RAM Solver Externo (MB)", "Pico de RAM do processo do solver", "MB"),
        "sens_gap": fig_sensitivity_gap(sens),
        "sens_k": fig_sensitivity_times(sens["cardinalidade"], "K", "Tempo vs cardinalidade K"),
        "sens_n": fig_sensitivity_times(sens["num_ativos"], "N", "Tempo vs número de ativos N"),
        "frontier": fig_frontier(sens),
    }


def _kpis(wf: WalkForwardResult, ev: ExactVsHeuristicResult) -> List[Dict[str, str]]:
    perf = wf.performance
    ex = ev.resources.iloc[0]
    seeds = ev.ga_seeds
    ga_time = seeds["Tempo de Parede (s)"].mean()
    best = perf["Sharpe"].idxmax()
    return [
        {"label": "Gap médio do AG ao ótimo", "value": f"{seeds['Gap vs Ótimo (%)'].mean():.2f}%",
         "note": f"{len(seeds)} sementes · melhor {seeds['Gap vs Ótimo (%)'].min():.2f}%"},
        {"label": "Tempo Couenne vs AG", "value": f"{ex['Tempo de Parede (s)']:.1f} s / {ga_time:.1f} s",
         "note": "ótimo provado vs heurística"},
        {"label": "Melhor Sharpe fora da amostra", "value": f"{perf.loc[best, 'Sharpe']:.2f}", "note": best},
        {"label": "Sharpe: ML vs média histórica",
         "value": f"{perf.loc[STRATEGIES[0], 'Sharpe']:.2f} / {perf.loc[STRATEGIES[1], 'Sharpe']:.2f}",
         "note": "mesmo otimizador, entrada μ diferente"},
        {"label": "IC médio da previsão ML", "value": f"{wf.forecast_quality.iloc[0]['IC de Spearman médio']:+.3f}",
         "note": "0 = sem poder preditivo"},
    ]


def _table_html(df: pd.DataFrame, pct_cols: List[str] = (), dec: int = 3) -> str:
    out = df.copy()
    for c in out.columns:
        if c in pct_cols:
            out[c] = out[c].map(lambda v: f"{v * 100:.1f}%")
        elif pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].map(lambda v: "—" if pd.isna(v) else f"{v:.{dec}f}")
    return out.to_html(classes="tbl", border=0, escape=True)


_CSS = """
:root{--surface:#f4f3ef;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e6e5e0;--accent:#2a78d6}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--surface:#121211;--card:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#33322f;--accent:#3987e5}}
:root[data-theme="dark"]{--surface:#121211;--card:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#33322f;--accent:#3987e5}
*{box-sizing:border-box}body{margin:0;background:var(--surface);color:var(--ink);font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5}
main{max-width:1240px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;margin:40px 0 4px}p.lead,p.sub{color:var(--ink2);margin:0 0 16px;max-width:80ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:24px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi .l{font-size:12px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}.kpi .v{font-size:24px;font-weight:650;margin:4px 0;font-variant-numeric:tabular-nums}.kpi .n{font-size:12px;color:var(--ink2)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px;min-width:0;overflow:hidden}
.tblwrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin-top:12px}
.tbl{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}.tbl th,.tbl td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.tbl th:first-child,.tbl td:first-child{text-align:left}.tbl thead th{color:var(--ink2);font-weight:600}
footer{margin-top:48px;color:var(--ink2);font-size:13px}
"""

_DARK_JS = """
(function(){
  var L=%s, D=%s;
  function isDark(){var t=document.documentElement.getAttribute('data-theme');
    if(t)return t==='dark';return window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches;}
  function swap(c){var i=L.indexOf(c);return i<0?c:D[i];}
  function apply(){ if(!window.Plotly)return;
    document.querySelectorAll('.js-plotly-plot').forEach(function(g){Plotly.Plots.resize(g);});
    if(!isDark())return;
    document.querySelectorAll('.js-plotly-plot').forEach(function(g){
      var u={'paper_bgcolor':'#1a1a19','plot_bgcolor':'#1a1a19','font.color':'#c3c2b7',
        'title.font.color':'#f0efec','legend.font.color':'#c3c2b7','hoverlabel.bgcolor':'#262624','hoverlabel.font.color':'#f0efec'};
      Object.keys(g.layout).forEach(function(k){ if(/^[xy]axis[0-9]*$/.test(k)){
        u[k+'.gridcolor']='#33322f'; u[k+'.linecolor']='#33322f'; u[k+'.zerolinecolor']='#4a4945';}});
      (g.layout.annotations||[]).forEach(function(a,i){u['annotations['+i+'].font.color']='#c3c2b7';});
      Plotly.relayout(g,u);
      (g.data||[]).forEach(function(tr,i){var u={};
        if(tr.line&&tr.line.color)u['line.color']=swap(tr.line.color);
        if(tr.marker&&typeof tr.marker.color==='string')u['marker.color']=swap(tr.marker.color);
        if(tr.marker&&Array.isArray(tr.marker.color))u['marker.color']=[tr.marker.color.map(swap)];
        if(Object.keys(u).length)Plotly.restyle(g,u,[i]);});
    });}
  window.addEventListener('load',apply);
  window.addEventListener('resize',function(){document.querySelectorAll('.js-plotly-plot').forEach(function(g){Plotly.Plots.resize(g);});});
})();
"""


def build_dashboard_html(
    wf: WalkForwardResult,
    ev: ExactVsHeuristicResult,
    grid: pd.DataFrame,
    sens: Dict[str, pd.DataFrame],
    out_path: str | Path,
    figures: Dict[str, go.Figure] | None = None,
) -> Path:
    """# FR-09, Course PDF Stage 6: Write the self-contained dashboard HTML file."""
    figs = figures or build_figures(wf, ev, grid, sens)
    cfg = {"displaylogo": False, "responsive": True}

    def div(name: str) -> str:
        return '<div class="card">' + figs[name].to_html(full_html=False, include_plotlyjs=False, config=cfg) + "</div>"

    kpis = "".join(
        f'<div class="kpi"><div class="l">{html.escape(k["label"])}</div><div class="v">{html.escape(k["value"])}</div>'
        f'<div class="n">{html.escape(k["note"])}</div></div>' for k in _kpis(wf, ev)
    )
    perf_pct = ["Retorno Anual (CAGR)", "Volatilidade Anual", "Máx. Drawdown", "CVaR 95% Diário"]
    res_cols = ["Método", "Objetivo", "Gap vs Ótimo (%)", "Tempo de Parede (s)", "Tempo de CPU (s)",
                "Uso de CPU (%)", "RAM Solver Externo (MB)", "Pico Heap Python (MB)"]
    js_ver = plotly.offline.get_plotlyjs_version()
    start = wf.rebalance_dates[0].strftime("%m/%Y")
    end = wf.wealth.index[-1].strftime("%m/%Y")

    page = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel Carteira Cripto</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@{js_ver}/plotly.min.js"></script>
<style>{_CSS}</style></head><body><main>
<h1>Otimização de carteiras de criptomoedas: painel da A2</h1>
<p class="lead">Seleção de carteira com limite de cardinalidade (K ativos, pesos entre 5% e 40%) sobre 19 criptoativos, 2021 a 2024.
Compara a solução exata (Pyomo + Couenne) com o Algoritmo Genético e valida o modelo em um backtest fora da amostra
({start} a {end}) com previsões de Machine Learning.</p>
<div class="kpis">{kpis}</div>

<h2>Etapa 4 · O modelo otimizado em um pipeline real</h2>
<p class="sub">Rebalanceamento a cada 30 dias. Em cada data o modelo só usa dados disponíveis até ali; custo de transação de 0,1% sobre o giro.</p>
<div class="grid2">{div("wealth")}{div("drawdown")}</div>
<div class="tblwrap">{_table_html(wf.performance, perf_pct)}</div>
<div class="grid2" style="margin-top:12px">{div("ic")}{div("allocation")}</div>
<div class="tblwrap">{_table_html(wf.forecast_quality, dec=4)}</div>

<h2>Etapa 5 · Exato x metaheurística</h2>
<p class="sub">Couenne prova o ótimo do MINLP; a relaxação contínua (Ipopt) dá um limitante inferior. O AG roda com {len(ev.ga_seeds)} sementes.</p>
<div class="grid2">{div("time")}{div("ram")}</div>
<div class="tblwrap">{_table_html(ev.resources[res_cols].set_index("Método"), dec=4)}</div>
<div class="grid2" style="margin-top:12px">{div("conv_gap")}{div("conv_div")}</div>
<div class="grid2" style="margin-top:12px">{div("grid")}{div("frontier")}</div>
<div style="margin-top:12px">{div("sens_gap")}</div>
<div class="grid2" style="margin-top:12px">{div("sens_k")}{div("sens_n")}</div>

<footer>Gerado pelo pacote <code>portfolio_opt</code> (notebook a2_colab_pt.ipynb). Dados: preços diários públicos (Yahoo Finance), uso acadêmico.</footer>
</main><script>{_DARK_JS % (json.dumps(LIGHT), json.dumps(DARK))}</script></body></html>"""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
