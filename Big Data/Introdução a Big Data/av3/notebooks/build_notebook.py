"""Gera notebooks/AV3_Evidencias_Pipeline.ipynb (as células ficam versionadas aqui).

Execução: ./scripts/run_notebook.sh. O notebook roda dentro da rede mybridge
e consulta cada componente ao vivo; nenhuma saída fica fixa no código.
"""
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

cells = [
    md("""# AV3 – Pipeline de Dados Air Quality: evidências de execução
**Disciplina:** Big Data (CEUB), Prof. Klayton R. Castro

Este notebook é executado **dentro da rede Docker `mybridge`** e consulta cada componente da arquitetura ao vivo:
MinIO, Kafka, Delta Lake (Bronze/Silver/Gold), Cassandra, Redis, API FastAPI e o histórico de execuções do Airflow.
Todas as saídas abaixo vêm da execução real."""),
    code("""import json, time, warnings
from datetime import datetime, timezone
import pandas as pd
import matplotlib.pyplot as plt
import requests
warnings.filterwarnings("ignore")
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 20)
import settings, infra_check, cassandra_admin, reporting
print("Executado em", datetime.now(timezone.utc).isoformat(timespec="seconds"))"""),

    md("## 1. Ambiente: comunicação entre os contêineres na rede `mybridge`"),
    code("apps = infra_check.run()"),

    md("## 2. Origem e ingestão: CSV no MinIO e tópicos Kafka"),
    code("""s3 = settings.s3_client()
head = s3.head_object(Bucket=settings.BUCKET, Key=settings.SOURCE_KEY)
print(f"s3://{settings.BUCKET}/{settings.SOURCE_KEY}: {head['ContentLength']:,} bytes, ETag {head['ETag']}")
raw = s3.get_object(Bucket=settings.BUCKET, Key=settings.SOURCE_KEY)["Body"].read().decode()
print("\\nPrimeiras linhas do CSV original (UCI):")
print("\\n".join(raw.splitlines()[:3]))"""),
    code("""from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP})
c = Consumer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP, "group.id": "av3-notebook", "enable.auto.commit": False})
rows = []
for topic, meta in admin.list_topics(timeout=10).topics.items():
    if topic.startswith("__"):
        continue
    for p in sorted(meta.partitions):
        lo, hi = c.get_watermark_offsets(TopicPartition(topic, p), timeout=10)
        rows.append({"tópico": topic, "partição": p, "offset_inicial": lo, "offset_final": hi, "mensagens": hi - lo})
pd.DataFrame(rows)"""),
    code("""def peek(topic, n=2, partition=0, from_end=True):
    lo, hi = c.get_watermark_offsets(TopicPartition(topic, partition), timeout=10)
    start = max(lo, hi - n) if from_end else lo
    c.assign([TopicPartition(topic, partition, start)])
    out = []
    while len(out) < min(n, hi - start):
        m = c.poll(5)
        if m is None: break
        out.append(json.loads(m.value()))
    return out
print("Mensagem em sensor_raw (JSON publicado pelo Producer):")
print(json.dumps(peek("sensor_raw", 1, from_end=False)[0], indent=2, ensure_ascii=False))
print("\\nÚltimos alertas em sensor_alerts:")
for a in peek("sensor_alerts", 3): print(a)"""),

    md("## 3. Lakehouse Delta Lake no MinIO (lido com `deltalake`, sem Spark)"),
    code("""from deltalake import DeltaTable
def dt(path): return DeltaTable(settings.to_s3_uri(path), storage_options=settings.delta_storage_options())
tables = {"bronze/sensor_raw": settings.BRONZE_PATH, "silver/airquality": settings.SILVER_PATH,
          "gold/daily_summary": settings.GOLD_DAILY_PATH, "gold/hourly_profile": settings.GOLD_HOURLY_PATH,
          "gold/alerts": settings.GOLD_ALERTS_PATH}
summary = []
for name, path in tables.items():
    t = dt(path)
    summary.append({"tabela": name, "versão": t.version(), "arquivos": len(t.files()),
                    "linhas": t.to_pyarrow_dataset().count_rows(),
                    "partições": ", ".join(t.metadata().partition_columns) or "-"})
pd.DataFrame(summary)"""),
    code("""bronze = dt(settings.BRONZE_PATH).to_pandas(columns=["bronze_run_id", "kafka_partition", "kafka_offset", "raw_value"])
print("Bronze guarda o JSON bruto exatamente como chegou do Kafka:")
print(bronze.iloc[0]["raw_value"][:300], "...")
bronze.groupby("bronze_run_id").size().rename("mensagens por carga").to_frame()"""),
    code("""silver_dt = dt(settings.SILVER_PATH)
silver = silver_dt.to_pandas()
print(silver.dtypes.to_string())
silver.sort_values("event_ts").head(5)[["event_ts", "co_mg_m3", "no2_ug_m3", "benzene_ug_m3", "temperature_c",
                                        "relative_humidity_pct", "missing_measures", "run_id"]]"""),
    md("**Histórico e time travel do Delta.** Cada carga gera uma versão. As versões anteriores continuam consultáveis."),
    code("""hist = pd.DataFrame(silver_dt.history())[["version", "timestamp", "operation", "operationMetrics"]]
hist["timestamp"] = pd.to_datetime(hist["timestamp"], unit="ms")
hist["métricas"] = hist["operationMetrics"].apply(lambda m: {k: m[k] for k in m if k in (
    "numOutputRows", "numTargetRowsInserted", "numTargetRowsUpdated", "numSourceRows")} if m else {})
display(hist.drop(columns="operationMetrics"))
v0 = DeltaTable(settings.to_s3_uri(settings.SILVER_PATH), version=0, storage_options=settings.delta_storage_options())
print(f"Silver na versão 0: {v0.to_pyarrow_dataset().count_rows()} linhas | versão atual ({silver_dt.version()}): {len(silver)} linhas")
print("CHECK constraints:", {k.split('.')[-1]: v for k, v in silver_dt.metadata().configuration.items() if 'constraints' in k})"""),

    md("## 4. Qualidade dos dados: relatórios gerados pelo pipeline"),
    code("""runs = cassandra_admin.connect(retries=3, wait=2)[1].execute(
    "SELECT run_id, status FROM airquality.pipeline_runs WHERE pipeline='pipeline_airquality' LIMIT 1").one()
RUN = runs.run_id
print("Última execução registrada:", RUN, runs.status)
silver_rep = reporting.get_report(RUN, "silver")
q = pd.DataFrame({"-200 → nulo": silver_rep["sentinel_minus_200_to_null"],
                  "fora da faixa → nulo": pd.Series(silver_rep["out_of_range_to_null"])}).fillna(0).astype(int)
print({k: silver_rep[k] for k in ("input_messages", "malformed_messages", "invalid_timestamp",
                                  "duplicates_in_batch", "rows_inserted", "rows_updated", "rows_unchanged", "rows_total")})
q"""),
    code("""val = reporting.get_report(RUN, "validation")
print(f"Validação: {val['status']} ({val['checks_passed']}/{val['checks_total']})")
pd.DataFrame(val["checks"])[["layer", "check", "ok", "detail"]]"""),

    md("## 5. Camada de serviço: Apache Cassandra (modelagem orientada a consultas)"),
    code("""cluster, cs = cassandra_admin.connect(retries=3, wait=2)
ks = settings.CASSANDRA_KEYSPACE
counts = {t: cs.execute(f"SELECT COUNT(*) FROM {ks}.{t}", timeout=120).one()[0]
          for t in ["readings_by_day", "daily_summary", "hourly_profile", "alerts_by_month", "latest_readings", "pipeline_runs"]}
pd.Series(counts, name="linhas").to_frame()"""),
    code("""print("Q1: leituras de um dia (1 partição)")
display(pd.DataFrame(list(cs.execute(f"SELECT event_ts, co_mg_m3, no2_ug_m3, temperature_c, source FROM {ks}.readings_by_day WHERE day='2004-11-17' LIMIT 6"))))
print("Q4: alertas de um mês, mais recentes primeiro")
display(pd.DataFrame(list(cs.execute(f"SELECT * FROM {ks}.alerts_by_month WHERE month='2005-02' LIMIT 6"))))
print("Q6: histórico de execuções da DAG")
display(pd.DataFrame(list(cs.execute(f"SELECT started_at, run_id, status, duration_s, rows_silver, rows_inserted, rows_updated, alerts, checks_passed, checks_total FROM {ks}.pipeline_runs WHERE pipeline='pipeline_airquality' LIMIT 5"))))"""),

    md("## 6. API FastAPI com cache Redis"),
    code("""API = settings.API_URL
import redis; r = redis.Redis(host=settings.REDIS_HOST)
for k in r.scan_iter("api:summary:*"): r.delete(k)   # força MISS na primeira chamada
for i in (1, 2, 3):
    t0 = time.perf_counter(); resp = requests.get(f"{API}/api/v1/summary"); ms = (time.perf_counter() - t0) * 1000
    print(f"chamada {i}: X-Cache={resp.headers['X-Cache']:4}  {ms:6.1f} ms")
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
print("cache:", requests.get(f"{API}/cache/stats").json())"""),
    code("""prof = pd.DataFrame(requests.get(f"{API}/api/v1/profile/hourly", params={"profile": "all"}).json()).sort_values("hour")
wk = pd.DataFrame(requests.get(f"{API}/api/v1/profile/hourly", params={"profile": "weekend"}).json()).sort_values("hour")
daily = pd.DataFrame(requests.get(f"{API}/api/v1/daily").json()); daily["day"] = pd.to_datetime(daily["day"])
fig, ax = plt.subplots(1, 2, figsize=(14, 4))
ax[0].plot(prof["hour"], prof["co_avg"], marker="o", label="todos os dias")
ax[0].plot(wk["hour"], wk["co_avg"], marker=".", ls="--", label="fim de semana")
ax[0].set(title="CO médio por hora do dia (API → Cassandra)", xlabel="hora", ylabel="mg/m³"); ax[0].legend()
ax[1].bar(daily["day"], daily["alerts"], width=1.0, color="tab:red")
ax[1].set(title="Alertas por dia", ylabel="alertas")
plt.tight_layout(); plt.show()"""),

    md("## 7. Processamento contínuo (Spark Structured Streaming)"),
    code("""st = requests.get(f"{API}/api/v1/stream/status").json()
print(json.dumps(st, indent=2))
latest = pd.DataFrame(requests.get(f"{API}/api/v1/latest", params={"limit": 8}).json())
latest[["received_at", "event_ts", "co_mg_m3", "no2_ug_m3", "temperature_c", "alert_rules"]] if not latest.empty else "sem leituras de streaming"
"""),
    code("cluster.shutdown(); c.close(); print('Fim das evidências.')"),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"}})
nbf.write(nb, "/work/notebooks/AV3_Evidencias_Pipeline.ipynb")
print("notebook gerado")
