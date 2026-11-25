"""Regras de alerta de qualidade do ar (fonte única para lote, streaming e API).

Os limiares foram escolhidos a partir da distribuição real do dataset
(NO2 > 200: 386 horas; CO > 10: 5 horas; média móvel 8h de CO > 5: 145 horas).
"""
RULES = [
    {
        "rule": "NO2_1H", "column": "no2_ug_m3", "threshold": 200.0, "window_hours": 1, "severity": "alta",
        "description": "NO2 horário acima de 200 µg/m³",
        "reference": "Valor-limite horário de NO2 da União Europeia (Diretiva 2008/50/CE)",
    },
    {
        "rule": "CO_1H", "column": "co_mg_m3", "threshold": 10.0, "window_hours": 1, "severity": "alta",
        "description": "CO horário acima de 10 mg/m³",
        "reference": "Limiar crítico usado no laboratório de referência da disciplina (CO > 10)",
    },
    {
        "rule": "CO_8H", "column": "co_mg_m3", "threshold": 5.0, "window_hours": 8, "severity": "moderada",
        "description": "Média móvel de 8h de CO acima de 5 mg/m³ (mínimo de 6 leituras na janela)",
        "reference": "Limiar de atenção do projeto: metade do valor-limite europeu de 10 mg/m³ (média 8h), "
                     "que não é excedido no período",
    },
]

ALERT_COLS = ["event_ts", "rule", "severity", "value", "threshold", "source", "alert_month"]


def _alerts_for(df, rule, value_col, source):
    from pyspark.sql import functions as F

    return df.filter(F.col(value_col) > rule["threshold"]).select(
        "event_ts",
        F.lit(rule["rule"]).alias("rule"),
        F.lit(rule["severity"]).alias("severity"),
        F.round(F.col(value_col), 3).alias("value"),
        F.lit(rule["threshold"]).alias("threshold"),
        F.lit(source).alias("source"),
        F.date_format("event_ts", "yyyy-MM").alias("alert_month"),
    )


def instant_alerts(df, source):
    """Regras de 1 hora: avaliáveis leitura a leitura, inclusive no streaming."""
    parts = [_alerts_for(df, r, r["column"], source) for r in RULES if r["window_hours"] == 1]
    out = parts[0]
    for p in parts[1:]:
        out = out.unionByName(p)
    return out


def all_alerts(df, source="batch"):
    """Regras de 1h + regras de janela móvel (exigem o histórico, por isso só no lote)."""
    from pyspark.sql import Window
    from pyspark.sql import functions as F

    out = instant_alerts(df, source)
    ts = F.col("event_ts").cast("long")
    for r in RULES:
        if r["window_hours"] > 1:
            w = Window.orderBy(ts).rangeBetween(-(r["window_hours"] - 1) * 3600, 0)
            rolled = (
                df.select("event_ts", r["column"])
                .withColumn("_avg", F.avg(r["column"]).over(w))
                .withColumn("_n", F.count(r["column"]).over(w))
                .filter(F.col("_n") >= 6)
            )
            out = out.unionByName(_alerts_for(rolled, r, "_avg", source))
    return out
