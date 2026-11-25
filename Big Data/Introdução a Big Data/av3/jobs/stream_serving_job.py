"""Streaming: Kafka -> Spark Structured Streaming -> Cassandra + Kafka (alertas).

Caminho de tempo real, que complementa o lote orquestrado pelo Airflow:
- consome o tópico sensor_raw continuamente (micro-lotes de 10 s)
- aplica a MESMA transformação da Silver (transforms.py)
- grava no Cassandra: latest_readings (visão ao vivo) e readings_by_day (upsert)
- avalia as regras de alerta instantâneas (alert_rules.py) e grava os alertas no
  Cassandra (alerts_by_month) e no tópico Kafka sensor_alerts
- registra o status de cada micro-lote no Redis (lido pela API / dashboard)

Checkpoint no MinIO: depois de uma reinicialização, retoma do último offset
processado, sem perder nem reprocessar mensagens.
"""
import json
from datetime import datetime, timezone

from pyspark.sql import functions as F

import alert_rules
import settings
import transforms
from spark_common import build_spark


def cassandra_write(df, table):
    (df.write.format("org.apache.spark.sql.cassandra")
       .options(keyspace=settings.CASSANDRA_KEYSPACE, table=table).mode("append").save())


def process_batch(batch_df, batch_id):
    batch_df.persist()
    n = batch_df.count()
    if n == 0:
        batch_df.unpersist()
        return

    alerts = alert_rules.instant_alerts(batch_df, source="stream").cache()
    rules_per_reading = alerts.groupBy("event_ts").agg(F.concat_ws(",", F.collect_set("rule")).alias("alert_rules"))

    cassandra_write(batch_df.select(
        F.col("event_date").alias("day"), "event_ts", "hour", "co_mg_m3", "nmhc_ug_m3", "benzene_ug_m3", "nox_ppb",
        "no2_ug_m3", "temperature_c", "relative_humidity_pct", "absolute_humidity", "missing_measures",
        F.lit("stream").alias("source"), "run_id"), "readings_by_day")

    cassandra_write(batch_df.join(rules_per_reading, "event_ts", "left").select(
        F.lit(settings.SENSOR_ID).alias("sensor_id"), F.col("received_at"), "event_ts", "co_mg_m3", "no2_ug_m3",
        "nox_ppb", "benzene_ug_m3", "temperature_c", "relative_humidity_pct",
        F.coalesce("alert_rules", F.lit("")).alias("alert_rules")), "latest_readings")

    n_alerts = alerts.count()
    if n_alerts:
        cassandra_write(alerts.select(F.col("alert_month").alias("month"), "event_ts", "rule", "severity", "value",
                                      "threshold", "source"), "alerts_by_month")
        (alerts.select(F.col("rule").alias("key"), F.to_json(F.struct(
            F.lit(settings.SENSOR_ID).alias("sensor_id"),
            F.date_format("event_ts", "yyyy-MM-dd'T'HH:mm:ss").alias("event_ts"),
            "rule", "severity", "value", "threshold", "source")).alias("value"))
            .write.format("kafka").option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
            .option("topic", settings.KAFKA_ALERTS_TOPIC).save())

    last = batch_df.agg(F.max("event_ts").alias("ts")).first()["ts"]
    status = {"batch_id": batch_id, "rows": n, "alerts": n_alerts, "last_event_ts": str(last),
              "processed_at": datetime.now(timezone.utc).isoformat()}
    try:
        import redis

        r = redis.Redis(host=settings.REDIS_HOST, decode_responses=True)
        r.set("stream:status", json.dumps(status))
        r.incrby("stream:rows_total", n)
        r.incrby("stream:alerts_total", n_alerts)
    except Exception as exc:  # noqa: BLE001 - Redis é observabilidade; não derruba o stream
        print(f"Aviso: não foi possível atualizar o Redis: {exc}")
    print(f"micro-lote {batch_id}: {n} leituras, {n_alerts} alertas, último evento {last}", flush=True)
    alerts.unpersist()
    batch_df.unpersist()


def main():
    import cassandra_admin

    cassandra_admin.ensure_schema()
    spark = build_spark("av3-stream-serving")

    src = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
        .option("subscribe", settings.KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 500)
        .option("failOnDataLoss", "false")
        .load()
    )
    parsed = transforms.parse(src.select(F.col("value").cast("string").alias("raw_value"),
                                         F.col("timestamp").alias("received_at")),
                              "raw_value", keep=("received_at",))
    readings = transforms.with_derived(
        transforms.typed(parsed.filter(~F.col("_malformed")).drop("_malformed")).filter(F.col("event_ts").isNotNull())
    )

    query = (
        readings.writeStream.foreachBatch(process_batch)
        .option("checkpointLocation", settings.STREAM_CHECKPOINT)
        .trigger(processingTime="10 seconds")
        .queryName("airquality_stream_serving")
        .start()
    )
    print(f"Streaming iniciado (checkpoint {settings.STREAM_CHECKPOINT})", flush=True)
    query.awaitTermination()


if __name__ == "__main__":
    main()
