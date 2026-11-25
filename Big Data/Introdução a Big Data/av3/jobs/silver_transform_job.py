"""Silver: Bronze -> dados tratados e tipados (Delta Lake, particionado por ano/mês).

- interpreta o JSON bruto da Bronze desta execução
- trata valores (vírgula decimal, -200 -> nulo, faixa inválida -> nulo)
- converte data + hora em timestamp
- deduplica por timestamp do evento
- faz MERGE na Silver pela chave event_ts. Uma linha existente só é
  atualizada se alguma medida mudou: reprocessar os mesmos dados não altera
  nada (idempotência), e o run_id gravado aponta para a carga que trouxe o
  valor atual.
- protege a tabela com CHECK constraints do Delta: dado fora da regra é
  rejeitado na escrita.
"""
import argparse

from pyspark.sql import Window
from pyspark.sql import functions as F

import reporting
import settings
import transforms
from spark_common import build_spark, is_delta, last_operation

CONSTRAINTS = {
    "event_ts_not_null": "event_ts IS NOT NULL",
    "rh_range": "relative_humidity_pct IS NULL OR relative_humidity_pct BETWEEN 0 AND 100",
    "co_non_negative": "co_mg_m3 IS NULL OR co_mg_m3 >= 0",
    "no2_non_negative": "no2_ug_m3 IS NULL OR no2_ug_m3 >= 0",
}


def ensure_constraints(spark, path):
    """Adiciona as CHECK constraints que faltarem (idempotente).

    Roda em toda execução. Se uma tentativa anterior foi interrompida entre a
    criação da tabela e os ALTER TABLE, a próxima completa o que faltou.
    """
    props = {r["key"]: r["value"] for r in spark.sql(f"SHOW TBLPROPERTIES delta.`{path}`").collect()}
    existing = {k.split(".")[-1] for k in props if k.startswith("delta.constraints.")}
    added = []
    for name, expr in CONSTRAINTS.items():
        if name not in existing:
            spark.sql(f"ALTER TABLE delta.`{path}` ADD CONSTRAINT {name} CHECK ({expr})")
            added.append(name)
    if added:
        print(f"Constraints adicionadas na Silver: {added}")
    return sorted(existing | set(added))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    spark = build_spark("av3-silver-transform")
    bronze = spark.read.format("delta").load(settings.BRONZE_PATH).filter(F.col("bronze_run_id") == args.run_id)

    parsed = transforms.parse(bronze, "raw_value", keep=("kafka_partition", "kafka_offset")).cache()
    n_input = parsed.count()
    n_malformed = parsed.filter("_malformed").count()
    q = parsed.filter(~F.col("_malformed")).agg(*transforms.quality_counts(parsed)).first().asDict()
    sentinels = {k.split("__")[1]: v for k, v in q.items() if k.startswith("sentinel__")}
    out_of_range = {k.split("__")[1]: v for k, v in q.items() if k.startswith("range__")}

    typed = transforms.typed(parsed.filter(~F.col("_malformed")).drop("_malformed"))
    n_bad_ts = typed.filter(F.col("event_ts").isNull()).count()

    w = Window.partitionBy("event_ts").orderBy(F.col("ingested_at").desc(), F.col("kafka_offset").desc())
    batch = (
        transforms.with_derived(typed.filter(F.col("event_ts").isNotNull()))
        .withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")
        .withColumn("processed_at", F.current_timestamp())
        .select("event_ts", "event_date", "year", "month", "day", "hour", "day_of_week", "is_weekend",
                *transforms.MEASURE_COLS, "missing_measures",
                "run_id", "source_line", "kafka_partition", "kafka_offset", "ingested_at", "processed_at")
        .cache()
    )
    n_batch = batch.count()
    n_dupes = n_input - n_malformed - n_bad_ts - n_batch

    path = settings.SILVER_PATH
    if not is_delta(spark, path):
        batch.write.format("delta").partitionBy("year", "month").save(path)
        print(f"Tabela Silver criada em {path}")
        active = ensure_constraints(spark, path)
    else:
        from delta.tables import DeltaTable

        # Constraints antes do MERGE: dado que viole a regra é rejeitado na escrita.
        active = ensure_constraints(spark, path)

        changed = " OR ".join(f"NOT (t.{c} <=> s.{c})" for c in transforms.MEASURE_COLS)
        (DeltaTable.forPath(spark, path).alias("t")
            .merge(batch.alias("s"), "t.event_ts = s.event_ts")
            .whenMatchedUpdateAll(condition=changed)
            .whenNotMatchedInsertAll()
            .execute())
    op = last_operation(spark, path)
    if op["operation"] == "ADD CONSTRAINT":  # tabela recém-criada: a escrita é a versão anterior
        from delta.tables import DeltaTable

        hist = DeltaTable.forPath(spark, path).history().filter("operation <> 'ADD CONSTRAINT'").limit(1).collect()[0]
        op = {"version": hist["version"], "operation": hist["operation"], "metrics": dict(hist["operationMetrics"] or {})}
    m = op["metrics"]
    inserted = int(m.get("numTargetRowsInserted", m.get("numOutputRows", n_batch)))
    updated = int(m.get("numTargetRowsUpdated", 0))

    silver = spark.read.format("delta").load(path)
    n_total = silver.count()
    print("Amostra da Silver:")
    silver.orderBy("event_ts").select("event_ts", "co_mg_m3", "no2_ug_m3", "temperature_c",
                                      "relative_humidity_pct", "missing_measures").show(5, truncate=False)

    reporting.put_report(args.run_id, "silver", {
        "run_id": args.run_id,
        "path": path,
        "input_messages": n_input,
        "malformed_messages": n_malformed,
        "invalid_timestamp": n_bad_ts,
        "duplicates_in_batch": n_dupes,
        "batch_rows": n_batch,
        "rows_inserted": inserted,
        "rows_updated": updated,
        "rows_unchanged": n_batch - inserted - updated,
        "rows_total": n_total,
        "sentinel_minus_200_to_null": sentinels,
        "out_of_range_to_null": out_of_range,
        "constraints": {k: CONSTRAINTS[k] for k in active},
        "delta_version": op["version"],
        "delta_operation": op["operation"],
    })
    spark.stop()


if __name__ == "__main__":
    main()
