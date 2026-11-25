"""Transformações PySpark compartilhadas entre o lote (Silver) e o streaming.

Manter uma única implementação garante que a camada de lote e a de tempo
real produzam exatamente os mesmos valores para a mesma mensagem.
"""
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

RAW_FIELDS = [
    "date", "time", "co_gt", "pt08_s1_co", "nmhc_gt", "c6h6_gt", "pt08_s2_nmhc",
    "nox_gt", "pt08_s3_nox", "no2_gt", "pt08_s4_no2", "pt08_s5_o3", "t", "rh", "ah",
]

# coluna bruta -> (nome final, faixa física válida [min, max] ou None)
MEASURES = {
    "co_gt": ("co_mg_m3", (0, 50)),
    "nmhc_gt": ("nmhc_ug_m3", (0, 2000)),
    "c6h6_gt": ("benzene_ug_m3", (0, 100)),
    "nox_gt": ("nox_ppb", (0, 2000)),
    "no2_gt": ("no2_ug_m3", (0, 1000)),
    "pt08_s1_co": ("sensor_co_resp", None),
    "pt08_s2_nmhc": ("sensor_nmhc_resp", None),
    "pt08_s3_nox": ("sensor_nox_resp", None),
    "pt08_s4_no2": ("sensor_no2_resp", None),
    "pt08_s5_o3": ("sensor_o3_resp", None),
    "t": ("temperature_c", (-30, 60)),
    "rh": ("relative_humidity_pct", (0, 100)),
    "ah": ("absolute_humidity", (0, 5)),
}
MEASURE_COLS = [final for final, _ in MEASURES.values()]

ENVELOPE = StructType([
    StructField("run_id", StringType()),
    StructField("source", StringType()),
    StructField("source_line", IntegerType()),
    StructField("ingested_at", StringType()),
    StructField("payload", StructType([StructField(f, StringType()) for f in RAW_FIELDS])),
])


def raw_number(c):
    return F.regexp_replace(F.trim(F.col(c)), ",", ".").cast("double")


def parse(df, value_col="raw_value", keep=()):
    """Interpreta o JSON (envelope + payload). Linhas malformadas ficam com payload nulo."""
    m = F.from_json(F.col(value_col).cast("string"), ENVELOPE)
    return df.select(*keep, m.alias("m")).select(
        *keep,
        F.col("m.run_id").alias("run_id"),
        F.col("m.source_line").alias("source_line"),
        F.to_timestamp("m.ingested_at").alias("ingested_at"),
        F.col("m.payload").isNull().alias("_malformed"),
        *[F.col(f"m.payload.{f}").alias(f) for f in RAW_FIELDS],
    )


def quality_counts(parsed):
    """Expressões de agregação para o relatório de qualidade (antes do tratamento)."""
    exprs = []
    for raw, (final, rng) in MEASURES.items():
        n = raw_number(raw)
        exprs.append(F.sum((n == -200).cast("int")).alias(f"sentinel__{final}"))
        if rng:
            exprs.append(F.sum((n.isNotNull() & (n != -200) & ((n < rng[0]) | (n > rng[1]))).cast("int"))
                         .alias(f"range__{final}"))
    return exprs


def typed(parsed):
    """Tipagem e tratamento: vírgula decimal, -200 -> nulo, faixa inválida -> nulo, data+hora -> timestamp."""
    out = parsed
    for raw, (final, rng) in MEASURES.items():
        v = raw_number(raw)
        v = F.when(v == -200, None).otherwise(v)
        if rng:
            v = F.when(v.isNotNull() & ((v < rng[0]) | (v > rng[1])), None).otherwise(v)
        out = out.withColumn(final, v.cast("double"))
    out = out.withColumn(
        "event_ts", F.to_timestamp(F.concat_ws(" ", F.col("date"), F.col("time")), "dd/MM/yyyy HH.mm.ss")
    )
    return out.drop(*RAW_FIELDS)


def with_derived(df):
    return (
        df.withColumn("event_date", F.to_date("event_ts"))
        .withColumn("year", F.year("event_ts"))
        .withColumn("month", F.month("event_ts"))
        .withColumn("day", F.dayofmonth("event_ts"))
        .withColumn("hour", F.hour("event_ts"))
        .withColumn("day_of_week", F.date_format("event_ts", "EEE"))
        .withColumn("is_weekend", F.dayofweek("event_ts").isin(1, 7))
        .withColumn("missing_measures", sum(F.col(c).isNull().cast("int") for c in MEASURE_COLS))
    )
