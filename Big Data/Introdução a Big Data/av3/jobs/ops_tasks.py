"""Tarefas operacionais do fim da DAG: cache da API e registro da execução."""
import json
from datetime import datetime, timezone

import requests

import cassandra_admin
import reporting
import settings

WARM_ENDPOINTS = ["/api/v1/summary", "/api/v1/daily", "/api/v1/profile/hourly?profile=all",
                  "/api/v1/alerts?limit=200", "/api/v1/meta"]


def refresh_api_cache():
    """Invalida o cache Redis da API (dados novos no Cassandra) e o pré-aquece."""
    import redis

    r = redis.Redis(host=settings.REDIS_HOST, decode_responses=True)
    keys = list(r.scan_iter("api:*"))
    if keys:
        r.delete(*keys)
    print(f"{len(keys)} chaves de cache invalidadas no Redis.")

    warmed = {}
    for ep in WARM_ENDPOINTS:
        for attempt in (1, 2):
            resp = requests.get(settings.API_URL + ep, timeout=30)
            resp.raise_for_status()
            warmed.setdefault(ep, []).append(resp.headers.get("X-Cache"))
    print("Pré-aquecimento (1ª chamada / 2ª chamada):")
    for ep, states in warmed.items():
        print(f"  {ep:40} {states[0]:5} -> {states[1]}")
    if not all(s[1] == "HIT" for s in warmed.values()):
        raise RuntimeError(f"Cache não respondeu HIT na segunda chamada: {warmed}")
    return {"invalidated": len(keys), "warmed": warmed}


def record_run(dag_run, run_id, **_):
    """Registra a execução no Cassandra (pipeline_runs) e no MinIO, com status real das tarefas.

    Roda com trigger_rule=all_done. Se alguma tarefa falhou, registra a falha e
    também falha, para o estado final da DAG continuar correto.
    """
    tis = [ti for ti in dag_run.get_task_instances() if ti.task_id != "record_run"]
    states = {ti.task_id: ti.state for ti in tis}
    failed = [t for t, s in states.items() if s not in ("success", "skipped")]
    status = "FAILED" if failed else "SUCCESS"
    started = dag_run.start_date
    duration = (datetime.now(timezone.utc) - started).total_seconds()

    def safe(stage):
        try:
            return reporting.get_report(run_id, stage)
        except Exception:  # noqa: BLE001 - etapa pode não ter rodado
            return {}

    bronze, silver, gold, validation = safe("bronze"), safe("silver"), safe("gold"), safe("validation")
    summary = {
        "run_id": run_id, "status": status, "started_at": started.isoformat(), "duration_s": round(duration, 1),
        "task_states": states, "failed_tasks": failed,
        "rows_bronze": bronze.get("slice_rows_in_table"), "rows_silver": silver.get("rows_total"),
        "rows_inserted": silver.get("rows_inserted"), "rows_updated": silver.get("rows_updated"),
        "alerts": (gold.get("tables") or {}).get("alerts", {}).get("rows"),
        "alerts_published": gold.get("alerts_published_to_kafka"),
        "checks_passed": validation.get("checks_passed"), "checks_total": validation.get("checks_total"),
    }
    reporting.put_report(run_id, "run_summary", summary)

    cluster, session = cassandra_admin.connect(retries=3, wait=2)
    try:
        session.execute(
            f"INSERT INTO {settings.CASSANDRA_KEYSPACE}.pipeline_runs (pipeline, started_at, run_id, status, "
            "duration_s, rows_bronze, rows_silver, rows_inserted, rows_updated, alerts, alerts_published, "
            "checks_passed, checks_total, details) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            ["pipeline_airquality", started, run_id, status, duration, summary["rows_bronze"], summary["rows_silver"],
             summary["rows_inserted"], summary["rows_updated"], summary["alerts"], summary["alerts_published"],
             summary["checks_passed"], summary["checks_total"], json.dumps(states)],
        )
    finally:
        cluster.shutdown()
    print(f"Execução registrada em {settings.CASSANDRA_KEYSPACE}.pipeline_runs: {status} em {duration:.0f}s")
    if failed:
        raise RuntimeError(f"Tarefas com falha nesta execução: {failed}")
    return summary
