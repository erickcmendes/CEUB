"""Validação ponta a ponta com leitores independentes do Spark.

- Lakehouse: lê as tabelas Delta com a biblioteca `deltalake` (delta-rs + PyArrow)
- Serving:   consulta o Cassandra com o driver Python
- Compara contagens entre producer, Bronze, Silver, Gold e Cassandra, e confere
  schema, integridade e o histórico de versões do Delta.

Falha (exceção) se qualquer verificação não passar, e a DAG fica vermelha.
"""
import sys
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import DeltaTable

import cassandra_admin
import reporting
import settings

EXPECTED_DOUBLE = ["co_mg_m3", "nmhc_ug_m3", "benzene_ug_m3", "nox_ppb", "no2_ug_m3", "temperature_c",
                   "relative_humidity_pct", "absolute_humidity"]


def delta(path):
    return DeltaTable(settings.to_s3_uri(path), storage_options=settings.delta_storage_options())


def cassandra_count(session, table):
    return session.execute(f"SELECT COUNT(*) FROM {settings.CASSANDRA_KEYSPACE}.{table}", timeout=120).one()[0]


def validate(run_id, produced):
    checks = []

    def check(layer, name, ok, detail):
        checks.append({"layer": layer, "check": name, "ok": bool(ok), "detail": detail})
        print(f"[{'OK ' if ok else 'ERRO'}] {layer:8} | {name}: {detail}")

    bronze_rep = reporting.get_report(run_id, "bronze")
    silver_rep = reporting.get_report(run_id, "silver")
    gold_rep = reporting.get_report(run_id, "gold")

    # ---------------- Bronze
    check("bronze", "mensagens do producer = fatia gravada na Bronze",
          bronze_rep["slice_rows_in_table"] == produced == bronze_rep["messages_read"],
          f"producer={produced} lidas={bronze_rep['messages_read']} na tabela={bronze_rep['slice_rows_in_table']}")
    bronze = delta(settings.BRONZE_PATH).to_pyarrow_table(
        columns=["kafka_topic", "kafka_partition", "kafka_offset", "kafka_timestamp"])
    keys = pc.binary_join_element_wise(
        bronze["kafka_topic"], pc.cast(bronze["kafka_partition"], pa.string()),
        pc.cast(bronze["kafka_offset"], pa.string()), pc.cast(bronze["kafka_timestamp"], pa.string()), "|")
    n_keys = len(pc.unique(keys))
    check("bronze", "nenhuma mensagem Kafka duplicada na Bronze", n_keys == bronze.num_rows,
          f"{bronze.num_rows} linhas, {n_keys} chaves únicas (histórico de todas as cargas)")

    # ---------------- Silver
    silver_dt = delta(settings.SILVER_PATH)
    silver = silver_dt.to_pyarrow_table()
    check("silver", "Silver não vazia", silver.num_rows > 0, f"{silver.num_rows} linhas, versão Delta {silver_dt.version()}")
    check("silver", "balanço do lote", silver_rep["batch_rows"] + silver_rep["malformed_messages"]
          + silver_rep["invalid_timestamp"] + silver_rep["duplicates_in_batch"] == silver_rep["input_messages"],
          f"{silver_rep['batch_rows']} + {silver_rep['malformed_messages']} + {silver_rep['invalid_timestamp']} + "
          f"{silver_rep['duplicates_in_batch']} = {silver_rep['input_messages']}")
    n_unique = len(pc.unique(silver["event_ts"]))
    check("silver", "event_ts único e sem nulos", n_unique == silver.num_rows and silver["event_ts"].null_count == 0,
          f"únicos={n_unique} nulos={silver['event_ts'].null_count}")
    check("silver", "event_ts é timestamp", pa.types.is_timestamp(silver.schema.field("event_ts").type),
          str(silver.schema.field("event_ts").type))
    wrong = [c for c in EXPECTED_DOUBLE if not pa.types.is_float64(silver.schema.field(c).type)]
    check("silver", "medidas são double", not wrong, f"fora do tipo: {wrong}" if wrong else "8 colunas float64")
    sentinels = sum(pc.sum(pc.equal(silver[c], -200.0)).as_py() or 0 for c in EXPECTED_DOUBLE)
    check("silver", "sem sentinela -200", sentinels == 0, f"ocorrências={sentinels}")
    mn, mx = pc.min_max(silver["event_ts"]).values()
    check("silver", "intervalo temporal", mn.as_py().year == 2004 and mx.as_py().year == 2005,
          f"{mn.as_py()} -> {mx.as_py()}")
    constraints = {k: v for k, v in silver_dt.metadata().configuration.items() if k.startswith("delta.constraints")}
    check("silver", "CHECK constraints ativas no Delta", len(constraints) >= 4, f"{sorted(constraints)}")
    history = silver_dt.history()
    check("silver", "histórico Delta (time travel)", len(history) >= 1,
          f"{len(history)} versões; última = {history[0]['operation']}")

    # ---------------- Gold
    daily = delta(settings.GOLD_DAILY_PATH).to_pyarrow_table()
    alerts = delta(settings.GOLD_ALERTS_PATH).to_pyarrow_table()
    hourly = delta(settings.GOLD_HOURLY_PATH).to_pyarrow_table()
    n_days = len(pc.unique(silver["event_date"]))
    check("gold", "1 linha por dia da Silver", daily.num_rows == n_days, f"gold={daily.num_rows} dias silver={n_days}")
    check("gold", "soma das leituras diárias = Silver", pc.sum(daily["readings"]).as_py() == silver.num_rows,
          f"{pc.sum(daily['readings']).as_py()} = {silver.num_rows}")
    check("gold", "soma de alertas diários = tabela de alertas", pc.sum(daily["alerts"]).as_py() == alerts.num_rows,
          f"{pc.sum(daily['alerts']).as_py()} = {alerts.num_rows}")
    check("gold", "perfil horário completo", hourly.num_rows == 72, f"{hourly.num_rows} linhas (3 perfis x 24h)")

    # ---------------- Cassandra
    cluster, session = cassandra_admin.connect(retries=3, wait=2)
    try:
        n_read = cassandra_count(session, "readings_by_day")
        n_daily = cassandra_count(session, "daily_summary")
        n_alerts = cassandra_count(session, "alerts_by_month")
        n_hourly = cassandra_count(session, "hourly_profile")
        check("cassandra", "readings_by_day = Silver", n_read == silver.num_rows, f"{n_read} = {silver.num_rows}")
        check("cassandra", "daily_summary = Gold", n_daily == daily.num_rows, f"{n_daily} = {daily.num_rows}")
        check("cassandra", "alerts_by_month = Gold", n_alerts == alerts.num_rows, f"{n_alerts} = {alerts.num_rows}")
        check("cassandra", "hourly_profile = Gold", n_hourly == hourly.num_rows, f"{n_hourly} = {hourly.num_rows}")
        # Consulta pontual comparando um valor entre Delta e Cassandra
        row = session.execute(f"SELECT co_mg_m3, no2_ug_m3 FROM {settings.CASSANDRA_KEYSPACE}.readings_by_day "
                              "WHERE day = '2004-03-10' AND event_ts = '2004-03-10 18:00:00+0000'").one()
        check("cassandra", "valor pontual igual ao da Silver (2004-03-10 18h)",
              row is not None and row.co_mg_m3 == 2.6 and row.no2_ug_m3 == 113.0,
              f"CO={row.co_mg_m3 if row else None} NO2={row.no2_ug_m3 if row else None}")
    finally:
        cluster.shutdown()

    failed = [c for c in checks if not c["ok"]]
    result = {
        "run_id": run_id,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "status": "FAILED" if failed else "PASSED",
        "summary": {
            "produced": produced, "bronze_slice_rows": bronze_rep["slice_rows_in_table"], "bronze_total_rows": bronze.num_rows, "silver_rows": silver.num_rows,
            "silver_inserted": silver_rep["rows_inserted"], "silver_updated": silver_rep["rows_updated"],
            "gold_days": daily.num_rows, "gold_alerts": alerts.num_rows,
            "alerts_published": gold_rep["alerts_published_to_kafka"],
        },
        "checks": checks,
    }
    reporting.put_report(run_id, "validation", result)
    if failed:
        raise ValueError(f"{len(failed)} verificação(ões) falharam: {[c['check'] for c in failed]}")
    print(f"VALIDAÇÃO OK: {len(checks)} verificações aprovadas.")
    return result


if __name__ == "__main__":
    validate(sys.argv[1], int(sys.argv[2]))
