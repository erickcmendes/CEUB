"""Job PySpark: Kafka (JSON) -> tratamento/transformação -> MinIO (Parquet).

Executado pelo Airflow via spark-submit no cluster Spark Standalone
(driver no contêiner do Airflow, executores no spark-worker).

Etapas:
 1. Lê do tópico apenas a fatia de offsets produzida nesta execução.
 2. Interpreta o JSON (envelope + payload) com schema explícito e conta
    mensagens malformadas.
 3. Trata os valores: vírgula decimal -> ponto, cast para double, sentinela
    -200 -> nulo, faixas físicas inválidas -> nulo.
 4. Converte data + hora ("10/03/2004" + "18.00.00") em timestamp; descarta
    registros sem timestamp válido.
 5. Remove duplicatas por timestamp do evento.
 6. Cria colunas derivadas (data, ano, mês, dia, hora, dia da semana, fim de
    semana, nº de medidas ausentes) e metadados de linhagem (run_id, linha de
    origem, partição/offset Kafka, horários de ingestão e processamento).
 7. Grava Parquet particionado por ano/mês no MinIO e relê para conferir.
 8. Publica um relatório JSON da execução em s3://air-quality/reports/.
"""
import argparse
import json
from datetime import datetime, timezone

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

import settings

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

ENVELOPE = StructType([
    StructField("run_id", StringType()),
    StructField("source", StringType()),
    StructField("source_line", IntegerType()),
    StructField("ingested_at", StringType()),
    StructField("payload", StructType([StructField(f, StringType()) for f in RAW_FIELDS])),
])


def build_spark():
    return (
        SparkSession.builder.appName("av3-airquality-kafka-to-minio")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.hadoop.fs.s3a.endpoint", settings.MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", settings.MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", settings.MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.sql.sources.partitionOverwriteMode", "static")
        .getOrCreate()
    )


def to_number(c):
    v = F.regexp_replace(F.trim(F.col(c)), ",", ".").cast("double")
    return F.when(v == -200, F.lit(None).cast("double")).otherwise(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--starting-offsets", default="earliest")
    ap.add_argument("--ending-offsets", default="latest")
    args = ap.parse_args()

    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    print(f"Spark {spark.version} | master={spark.sparkContext.master} | app={spark.sparkContext.applicationId}")
    print(f"Offsets: {args.starting_offsets} -> {args.ending_offsets}")

    # 1. Leitura em lote do Kafka
    kafka_df = (
        spark.read.format("kafka")
        .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
        .option("subscribe", settings.KAFKA_TOPIC)
        .option("startingOffsets", args.starting_offsets)
        .option("endingOffsets", args.ending_offsets)
        .load()
    )

    # 2. Interpretação do JSON
    parsed = kafka_df.select(
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.from_json(F.col("value").cast("string"), ENVELOPE).alias("m"),
    ).cache()
    n_input = parsed.count()
    n_malformed = parsed.filter(F.col("m").isNull() | F.col("m.payload").isNull()).count()

    flat = parsed.filter(F.col("m.payload").isNotNull()).select(
        "kafka_partition", "kafka_offset",
        F.col("m.run_id").alias("run_id"),
        F.col("m.source_line").alias("source_line"),
        F.to_timestamp("m.ingested_at").alias("ingested_at"),
        *[F.col(f"m.payload.{f}").alias(f) for f in RAW_FIELDS],
    )

    # 3. Tipagem e tratamento de valores
    typed = flat
    sentinel_exprs, range_exprs = [], []
    for raw, (final, rng) in MEASURES.items():
        num = to_number(raw)
        sentinel_exprs.append(F.sum((F.regexp_replace(F.trim(F.col(raw)), ",", ".").cast("double") == -200)
                                    .cast("int")).alias(final))
        if rng:
            out_of_range = num.isNotNull() & ((num < rng[0]) | (num > rng[1]))
            range_exprs.append(F.sum(out_of_range.cast("int")).alias(final))
            num = F.when(out_of_range, F.lit(None).cast("double")).otherwise(num)
        typed = typed.withColumn(final, num)

    sentinel_counts = flat.agg(*sentinel_exprs).first().asDict()
    range_counts = flat.agg(*range_exprs).first().asDict() if range_exprs else {}

    # 4. Data e hora -> timestamp
    typed = typed.withColumn(
        "event_ts", F.to_timestamp(F.concat_ws(" ", F.col("date"), F.col("time")), "dd/MM/yyyy HH.mm.ss")
    )
    n_bad_ts = typed.filter(F.col("event_ts").isNull()).count()
    typed = typed.filter(F.col("event_ts").isNotNull())

    # 5. Deduplicação por timestamp (mantém a ingestão mais recente)
    w = Window.partitionBy("event_ts").orderBy(F.col("ingested_at").desc(), F.col("kafka_offset").desc())
    deduped = typed.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")

    # 6. Colunas derivadas e metadados
    measure_cols = [final for final, _ in MEASURES.values()]
    final_df = (
        deduped
        .withColumn("event_date", F.to_date("event_ts"))
        .withColumn("year", F.year("event_ts"))
        .withColumn("month", F.month("event_ts"))
        .withColumn("day", F.dayofmonth("event_ts"))
        .withColumn("hour", F.hour("event_ts"))
        .withColumn("day_of_week", F.date_format("event_ts", "EEE"))
        .withColumn("is_weekend", F.dayofweek("event_ts").isin(1, 7))
        .withColumn("missing_measures", sum(F.col(c).isNull().cast("int") for c in measure_cols))
        .withColumn("processed_at", F.current_timestamp())
        .select(
            "event_ts", "event_date", "year", "month", "day", "hour", "day_of_week", "is_weekend",
            *measure_cols, "missing_measures",
            "run_id", "source_line", "kafka_partition", "kafka_offset", "ingested_at", "processed_at",
        )
    )

    # 7. Gravação em Parquet no MinIO e releitura
    out = settings.PROCESSED_URI_S3A
    (final_df.repartition("year", "month")
        .write.mode("overwrite").partitionBy("year", "month")
        .option("compression", "snappy").parquet(out))

    back = spark.read.parquet(out)
    n_written = back.count()
    n_duplicates = (n_input - n_malformed - n_bad_ts) - n_written

    print("\nSchema gravado:")
    back.printSchema()
    print("Amostra:")
    back.orderBy("event_ts").select("event_ts", "co_mg_m3", "no2_ug_m3", "temperature_c",
                                    "relative_humidity_pct", "missing_measures").show(5, truncate=False)
    print("Média mensal (consulta Spark SQL sobre o Parquet no MinIO):")
    back.createOrReplaceTempView("airquality")
    spark.sql("""
        SELECT year, month, COUNT(*) AS registros,
               ROUND(AVG(co_mg_m3), 2) AS co_medio, ROUND(AVG(no2_ug_m3), 1) AS no2_medio,
               ROUND(AVG(temperature_c), 1) AS temp_media
        FROM airquality GROUP BY year, month ORDER BY year, month
    """).show(20, truncate=False)

    ts_range = back.agg(F.min("event_ts").alias("min"), F.max("event_ts").alias("max")).first()
    report = {
        "run_id": args.run_id,
        "spark_app_id": spark.sparkContext.applicationId,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "output": out,
        "input_messages": n_input,
        "malformed_messages": n_malformed,
        "invalid_timestamp": n_bad_ts,
        "duplicates_removed": n_duplicates,
        "rows_written": n_written,
        "sentinel_minus_200_to_null": sentinel_counts,
        "out_of_range_to_null": range_counts,
        "event_ts_min": str(ts_range["min"]),
        "event_ts_max": str(ts_range["max"]),
        "partitions": [f"year={r.year}/month={r.month}" for r in
                       back.select("year", "month").distinct().orderBy("year", "month").collect()],
    }
    key = f"{settings.REPORTS_PREFIX}/run_id={args.run_id}/spark_report.json"
    settings.s3_client().put_object(Bucket=settings.BUCKET, Key=key,
                                    Body=json.dumps(report, indent=2).encode(), ContentType="application/json")
    print(f"Relatório salvo em s3://{settings.BUCKET}/{key}")
    print("SPARK_REPORT=" + json.dumps(report))
    spark.stop()


if __name__ == "__main__":
    main()
