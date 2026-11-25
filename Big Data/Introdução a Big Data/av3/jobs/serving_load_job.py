"""Serving: Silver e Gold (Delta) -> Apache Cassandra.

O Cassandra é a camada de consulta de baixa latência usada pela API. As
tabelas são modeladas a partir das consultas (ver cassandra/schema.cql), e
as escritas são upserts pela chave primária, então recarregar é idempotente.
"""
import argparse

from pyspark.sql import functions as F

import reporting
import settings
from spark_common import build_spark


def write(df, table):
    (df.write.format("org.apache.spark.sql.cassandra")
       .options(keyspace=settings.CASSANDRA_KEYSPACE, table=table)
       .mode("append").save())


def count_table(spark, table):
    return (spark.read.format("org.apache.spark.sql.cassandra")
            .options(keyspace=settings.CASSANDRA_KEYSPACE, table=table).load().count())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    spark = build_spark("av3-serving-load")
    silver = spark.read.format("delta").load(settings.SILVER_PATH)
    daily = spark.read.format("delta").load(settings.GOLD_DAILY_PATH)
    hourly = spark.read.format("delta").load(settings.GOLD_HOURLY_PATH)
    alerts = spark.read.format("delta").load(settings.GOLD_ALERTS_PATH)

    loads = {
        "readings_by_day": silver.select(
            F.col("event_date").alias("day"), "event_ts", "hour", "co_mg_m3", "nmhc_ug_m3", "benzene_ug_m3",
            "nox_ppb", "no2_ug_m3", "temperature_c", "relative_humidity_pct", "absolute_humidity",
            "missing_measures", F.lit("batch").alias("source"), "run_id"),
        "daily_summary": daily,
        "hourly_profile": hourly,
        "alerts_by_month": alerts.select(F.col("alert_month").alias("month"), "event_ts", "rule", "severity",
                                         "value", "threshold", "source"),
    }
    result = {}
    for table, df in loads.items():
        n = df.count()
        write(df, table)
        result[table] = {"rows_written": n}
        print(f"Cassandra {settings.CASSANDRA_KEYSPACE}.{table}: {n} linhas gravadas (upsert)")

    for table in loads:
        result[table]["rows_in_table"] = count_table(spark, table)

    print("Leitura de volta do Cassandra (readings_by_day, 2004-03-11, 3 primeiras horas):")
    (spark.read.format("org.apache.spark.sql.cassandra")
        .options(keyspace=settings.CASSANDRA_KEYSPACE, table="readings_by_day").load()
        .filter(F.col("day") == F.lit("2004-03-11").cast("date"))
        .select("day", "event_ts", "co_mg_m3", "no2_ug_m3", "temperature_c").orderBy("event_ts").show(3))

    reporting.put_report(args.run_id, "serving", {"run_id": args.run_id, "keyspace": settings.CASSANDRA_KEYSPACE,
                                                  "tables": result})
    spark.stop()


if __name__ == "__main__":
    main()
