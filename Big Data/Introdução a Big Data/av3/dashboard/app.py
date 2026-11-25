"""Dashboard Air Quality Analytics (Streamlit).

Consome exclusivamente a API FastAPI: o dashboard não acessa os bancos
diretamente, então toda leitura passa pela camada de integração e pelo cache.
"""
import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Air Quality Analytics", page_icon="🌫️", layout="wide")


@st.cache_data(ttl=30, show_spinner=False)
def get(path, **params):
    r = requests.get(f"{API}{path}", params={k: v for k, v in params.items() if v is not None}, timeout=30)
    r.raise_for_status()
    return r.json()


def live(path, **params):
    r = requests.get(f"{API}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


st.title("Air Quality Analytics")
st.caption("Pipeline MinIO → Kafka → Spark (Delta Lake) → Cassandra → FastAPI/Redis → Streamlit · "
           "dataset UCI Air Quality (cidade italiana, 2004–2005)")

try:
    meta = get("/api/v1/meta")
except Exception as exc:  # noqa: BLE001
    st.error(f"API indisponível ou sem dados ({exc}). Execute a DAG pipeline_airquality no Airflow.")
    st.stop()

first, last = date.fromisoformat(meta["first_day"]), date.fromisoformat(meta["last_day"])
with st.sidebar:
    st.header("Período")
    period = st.date_input("Intervalo", (first, last), min_value=first, max_value=last)
    start, end = (period if isinstance(period, tuple) and len(period) == 2 else (first, last))
    st.divider()
    st.subheader("Regras de alerta")
    for r in meta["alert_rules"]:
        st.markdown(f"**{r['rule']}** ({r['severity']})  \n{r['description']}  \n"
                    f"<small>{r['reference']}</small>", unsafe_allow_html=True)

tab_overview, tab_alerts, tab_day, tab_live, tab_ops = st.tabs(
    ["Visão geral", "Alertas", "Detalhe do dia", "Tempo real", "Pipeline"])

# --------------------------------------------------------------------------- visão geral
with tab_overview:
    s = get("/api/v1/summary", start=str(start), end=str(end))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Registros", f"{s['readings']:,}".replace(",", "."))
    c2.metric("Temperatura média", f"{s['temperature_avg_c']:.1f} °C".replace(".", ","))
    c3.metric("CO médio", f"{s['co_avg_mg_m3']:.2f} mg/m³".replace(".", ","))
    c4.metric("NO2 médio", f"{s['no2_avg_ug_m3']:.0f} µg/m³")
    c5.metric("Alertas", s["alerts"])

    left, right = st.columns(2)
    profile_name = left.radio("Perfil horário", ["all", "weekday", "weekend"], horizontal=True,
                              format_func={"all": "Todos os dias", "weekday": "Dias úteis",
                                           "weekend": "Fim de semana"}.get)
    prof = pd.DataFrame(get("/api/v1/profile/hourly", profile=profile_name)).sort_values("hour")
    fig = go.Figure()
    fig.add_scatter(x=prof["hour"], y=prof["co_avg"], name="CO (mg/m³)", mode="lines+markers")
    fig.add_scatter(x=prof["hour"], y=prof["no2_avg"], name="NO2 (µg/m³)", yaxis="y2", mode="lines")
    fig.update_layout(title="Concentração média por hora do dia", xaxis_title="hora",
                      yaxis=dict(title="CO (mg/m³)"), yaxis2=dict(title="NO2 (µg/m³)", overlaying="y", side="right"),
                      legend=dict(orientation="h", y=-0.2), height=380, margin=dict(t=50, b=10))
    left.plotly_chart(fig, use_container_width=True)

    daily = pd.DataFrame(get("/api/v1/daily", start=str(start), end=str(end)))
    daily["day"] = pd.to_datetime(daily["day"])
    fig2 = px.line(daily, x="day", y=["co_avg", "co_max"], title="CO diário (média e máximo)",
                   labels={"value": "mg/m³", "day": "", "variable": ""})
    fig2.update_layout(height=380, legend=dict(orientation="h", y=-0.2), margin=dict(t=50, b=10))
    right.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(daily, x="day", y="alerts", title="Alertas por dia", labels={"alerts": "alertas", "day": ""})
    fig3.update_layout(height=300, margin=dict(t=50, b=10))
    st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------------------------------- alertas
with tab_alerts:
    rule = st.selectbox("Regra", ["(todas)"] + [r["rule"] for r in meta["alert_rules"]])
    al = pd.DataFrame(get("/api/v1/alerts", start=str(start), end=str(end), limit=5000,
                          rule=None if rule == "(todas)" else rule))
    if al.empty:
        st.info("Nenhum alerta no período.")
    else:
        al["event_ts"] = pd.to_datetime(al["event_ts"])
        a1, a2 = st.columns([1, 2])
        a1.plotly_chart(px.pie(al, names="rule", title="Distribuição por regra", hole=0.45)
                        .update_layout(height=320), use_container_width=True)
        al["mês"] = al["event_ts"].dt.strftime("%Y-%m")
        a2.plotly_chart(px.histogram(al, x="mês", color="rule", title="Alertas por mês")
                        .update_layout(height=320), use_container_width=True)
        st.dataframe(al.sort_values("event_ts", ascending=False)[
            ["event_ts", "rule", "severity", "value", "threshold", "source"]],
            use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- dia
with tab_day:
    day = st.date_input("Dia", min(max(date(2004, 11, 17), first), last), min_value=first, max_value=last)
    try:
        rd = pd.DataFrame(get(f"/api/v1/readings/{day}"))
        rd["event_ts"] = pd.to_datetime(rd["event_ts"])
        figd = px.line(rd, x="event_ts", y=["co_mg_m3", "benzene_ug_m3"], markers=True,
                       title=f"CO e benzeno em {day}", labels={"value": "", "event_ts": ""})
        no2_limit = next(r["threshold"] for r in meta["alert_rules"] if r["rule"] == "NO2_1H")
        fign = px.bar(rd, x="event_ts", y="no2_ug_m3", title=f"NO2 em {day} (linha = limite {no2_limit:.0f})")
        fign.add_hline(y=no2_limit, line_dash="dash", line_color="red")
        d1, d2 = st.columns(2)
        d1.plotly_chart(figd, use_container_width=True)
        d2.plotly_chart(fign, use_container_width=True)
        st.dataframe(rd.drop(columns=["day"]), use_container_width=True, hide_index=True)
    except requests.HTTPError:
        st.warning(f"Sem leituras em {day}.")

# --------------------------------------------------------------------------- tempo real
with tab_live:
    st.caption("Leituras do simulador de sensor processadas pelo Spark Structured Streaming "
               "(atualiza a cada 10 s; perfil `streaming` do docker compose).")

    @st.fragment(run_every=10)
    def live_panel():
        status = live("/api/v1/stream/status")
        lt = pd.DataFrame(live("/api/v1/latest", limit=60))
        if lt.empty:
            st.info("Nenhuma leitura em tempo real. Suba o perfil: docker compose --profile streaming up -d")
            return
        lb = status.get("last_batch") or {}
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Leituras via streaming", status["rows_total"])
        k2.metric("Alertas via streaming", status["alerts_total"])
        k3.metric("Último micro-lote", lb.get("batch_id", "-"), f"{lb.get('rows', 0)} leituras")
        k4.metric("CO mais recente", f"{lt.iloc[0]['co_mg_m3'] or 0:.1f} mg/m³".replace(".", ","))
        lt["received_at"] = pd.to_datetime(lt["received_at"])
        lt = lt.sort_values("received_at")
        figl = px.line(lt, x="received_at", y=["co_mg_m3"], markers=True,
                       title="CO nas últimas leituras recebidas", labels={"value": "mg/m³", "received_at": "recebido em"})
        st.plotly_chart(figl, use_container_width=True)
        st.dataframe(lt.sort_values("received_at", ascending=False)[
            ["received_at", "event_ts", "co_mg_m3", "no2_ug_m3", "temperature_c", "alert_rules"]],
            use_container_width=True, hide_index=True)

    live_panel()

# --------------------------------------------------------------------------- pipeline
with tab_ops:
    h = live("/health")
    cs = live("/cache/stats")
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("API", h["status"])
    o2.metric("Cassandra", h["cassandra"])
    o3.metric("Cache hit ratio", f"{(cs['hit_ratio'] or 0) * 100:.0f}%", f"{cs['hits']} hits / {cs['misses']} misses")
    o4.metric("Chaves em cache", cs["keys"])
    runs = pd.DataFrame(live("/api/v1/pipeline/runs", limit=20))
    st.subheader("Execuções da DAG pipeline_airquality")
    if runs.empty:
        st.info("Nenhuma execução registrada ainda.")
    else:
        st.dataframe(runs[["started_at", "run_id", "status", "duration_s", "rows_bronze", "rows_silver",
                           "rows_inserted", "rows_updated", "alerts", "alerts_published", "checks_passed",
                           "checks_total"]], use_container_width=True, hide_index=True)
