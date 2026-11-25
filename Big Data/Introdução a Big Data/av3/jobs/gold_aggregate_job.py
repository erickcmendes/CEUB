"""Gold: Silver -> tabelas analíticas (Delta Lake) + publicação de alertas no Kafka.

- daily_summary:  indicadores diários (médias, máximos, completude, nº de alertas)
- hourly_profile: perfil médio por hora do dia (todos os dias / dias úteis / fim de semana)
- alerts:         violações das regras de alert_rules.py (inclui média móvel de 8h)

As tabelas Gold são recalculadas por completo a partir da Silver (overwrite).
As versões anteriores continuam acessíveis por time travel. Só os alertas de
leituras novas ou alteradas nesta execução são publicados no tópico
sensor_alerts. Em uma reexecução sem dados novos, nada é republicado.
"""
import argparse

from pyspark.sql import functions as F

import alert_rules
import reporting
import settings
from spark_common import build_spark, last_operation


def daily_summary(silver, alerts):
    alerts_per_day = alerts.groupBy(F.to_date("event_ts").alias("event_date")).agg(F.count("*").alias("alerts"))
    return (
        silver.groupBy("event_date", "year").agg(
            F.count("*").alias("readings"),
            F.round(F.avg("co_mg_m3"), 3).alias("co_avg"),
            F.round(F.max("co_mg_m3"), 3).alias("co_max"),
            F.round(F.avg("no2_ug_m3"), 2).alias("no2_avg"),
            F.round(F.max("no2_ug_m3"), 2).alias("no2_max"),
            F.round(F.avg("nox_ppb"), 2).alias("nox_avg"),
            F.round(F.avg("benzene_ug_m3"), 3).alias("benzene_avg"),
            F.round(F.avg("temperature_c"), 2).alias("temp_avg"),
            F.round(F.min("temperature_c"), 2).alias("temp_min"),
            F.round(F.max("temperature_c"), 2).alias("temp_max"),
            F.round(F.avg("relative_humidity_pct"), 2).alias("rh_avg"),
            F.round(F.avg(1 - F.col("missing_measures") / 13.0) * 100, 1).alias("completeness_pct"),
        )
        .join(alerts_per_day, "event_date", "left")
        .withColumn("alerts", F.coalesce("alerts", F.lit(0)).cast("int"))
        .withColumnRenamed("event_date", "day")
        .orderBy("day")
    )


def hourly_profile(silver):
    def agg(df, profile):
        return df.groupBy("hour").agg(
            F.round(F.avg("co_mg_m3"), 3).alias("co_avg"),
            F.round(F.avg("no2_ug_m3"), 2).alias("no2_avg"),
            F.round(F.avg("nox_ppb"), 2).alias("nox_avg"),
            F.round(F.avg("benzene_ug_m3"), 3).alias("benzene_avg"),
            F.round(F.avg("temperature_c"), 2).alias("temp_avg"),
            F.count("*").alias("readings"),
        ).withColumn("profile", F.lit(profile))

    return (agg(silver, "all")
            .unionByName(agg(silver.filter(~F.col("is_weekend")), "weekday"))
            .unionByName(agg(silver.filter(F.col("is_weekend")), "weekend")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    spark = build_spark("av3-gold-aggregate")
    silver = spark.read.format("delta").load(settings.SILVER_PATH).cache()
    n_silver = silver.count()

    alerts = alert_rules.all_alerts(silver, source="batch").cache()
    daily = daily_summary(silver, alerts).cache()
    hourly = hourly_profile(silver)

    results = {}
    for name, df, path, parts in [
        ("daily_summary", daily, settings.GOLD_DAILY_PATH, ["year"]),
        ("hourly_profile", hourly, settings.GOLD_HOURLY_PATH, []),
        ("alerts", alerts, settings.GOLD_ALERTS_PATH, ["alert_month"]),
    ]:
        w = df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
        if parts:
            w = w.partitionBy(*parts)
        w.save(path)
        op = last_operation(spark, path)
        results[name] = {"path": path, "rows": spark.read.format("delta").load(path).count(),
                         "delta_version": op["version"]}
        print(f"Gold {name}: {results[name]['rows']} linhas (versão Delta {op['version']})")

    print("Alertas por regra:")
    by_rule = {r["rule"]: r["count"] for r in alerts.groupBy("rule").count().orderBy("rule").collect()}
    print(by_rule)
    print("Dias com mais alertas:")
    daily.orderBy(F.desc("alerts"), "day").select("day", "readings", "co_avg", "no2_max", "alerts").show(5)

    # Publicação no Kafka: alertas de leituras inseridas/alteradas por esta execução
    run_rows = silver.filter(F.col("run_id") == args.run_id).select("event_ts")
    new_alerts = alerts.join(run_rows, "event_ts", "left_semi")
    n_published = new_alerts.count()
    if n_published:
        (new_alerts
            .select(F.col("rule").alias("key"),
                    F.to_json(F.struct(F.lit(settings.SENSOR_ID).alias("sensor_id"),
                                       F.date_format("event_ts", "yyyy-MM-dd'T'HH:mm:ss").alias("event_ts"),
                                       "rule", "severity", "value", "threshold", "source",
                                       F.lit(args.run_id).alias("run_id"))).alias("value"))
            .write.format("kafka")
            .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
            .option("topic", settings.KAFKA_ALERTS_TOPIC)
            .save())
    print(f"{n_published} alertas publicados no tópico {settings.KAFKA_ALERTS_TOPIC}")

    reporting.put_report(args.run_id, "gold", {
        "run_id": args.run_id,
        "silver_rows": n_silver,
        "tables": results,
        "alerts_by_rule": by_rule,
        "alerts_published_to_kafka": n_published,
        "rules": alert_rules.RULES,
    })
    spark.stop()


if __name__ == "__main__":
    main()
