"""Bronze: Kafka -> Delta Lake (dados brutos, sem interpretação).

Guarda cada mensagem exatamente como chegou (JSON em texto) com os metadados
do Kafka. Lê só a fatia de offsets produzida nesta execução e faz MERGE pela
identidade física da mensagem (tópico, partição, offset e timestamp do Kafka).
Se a tarefa for reexecutada, nada é duplicado. O timestamp entra na chave para
que um tópico recriado, com offsets reiniciados, não colida com o histórico.
"""
import argparse

from pyspark.sql import functions as F

import reporting
import settings
from spark_common import build_spark, is_delta, last_operation

KEY = ["kafka_topic", "kafka_partition", "kafka_offset", "kafka_timestamp"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--starting-offsets", required=True)
    ap.add_argument("--ending-offsets", required=True)
    args = ap.parse_args()

    spark = build_spark("av3-bronze-ingest")
    print(f"Offsets: {args.starting_offsets} -> {args.ending_offsets}")

    src = (
        spark.read.format("kafka")
        .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
        .option("subscribe", settings.KAFKA_TOPIC)
        .option("startingOffsets", args.starting_offsets)
        .option("endingOffsets", args.ending_offsets)
        .load()
    )
    bronze = src.select(
        F.lit(args.run_id).alias("bronze_run_id"),
        F.col("topic").alias("kafka_topic"),
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("timestamp").alias("kafka_timestamp"),
        F.col("key").cast("string").alias("kafka_key"),
        F.col("value").cast("string").alias("raw_value"),
        F.current_timestamp().alias("bronze_loaded_at"),
        F.to_date("timestamp").alias("ingest_date"),
    ).cache()
    n_read = bronze.count()

    path = settings.BRONZE_PATH
    if not is_delta(spark, path):
        bronze.write.format("delta").partitionBy("ingest_date").save(path)
        print(f"Tabela Bronze criada em {path}")
    else:
        from delta.tables import DeltaTable

        (DeltaTable.forPath(spark, path).alias("t")
            .merge(bronze.alias("s"),
                   " AND ".join(f"t.{k} = s.{k}" for k in KEY))
            .whenNotMatchedInsertAll()
            .execute())
    op = last_operation(spark, path)
    total = spark.read.format("delta").load(path)
    n_slice = total.join(bronze.select(*KEY), KEY, "left_semi").count()
    n_run = total.filter(F.col("bronze_run_id") == args.run_id).count()
    n_dupes = total.groupBy(*KEY).count().filter("count > 1").count()

    print("Amostra da Bronze (valor bruto):")
    total.join(bronze.select(*KEY), KEY, "left_semi").select(
        "kafka_partition", "kafka_offset", "kafka_key", F.substring("raw_value", 1, 90).alias("raw_value")
    ).show(3, truncate=False)

    reporting.put_report(args.run_id, "bronze", {
        "run_id": args.run_id,
        "path": path,
        "messages_read": n_read,
        "slice_rows_in_table": n_slice,
        "rows_for_run": n_run,
        "duplicate_keys_in_table": n_dupes,
        "rows_total": total.count(),
        "delta_version": op["version"],
        "delta_operation": op["operation"],
        "delta_metrics": op["metrics"],
    })
    if n_slice != n_read or n_dupes:
        raise RuntimeError(f"Bronze inconsistente: lidas {n_read}, presentes {n_slice}, chaves duplicadas {n_dupes}")
    spark.stop()


if __name__ == "__main__":
    main()
