"""API de dados de qualidade do ar (FastAPI).

Lê a camada de serviço no Cassandra. As consultas analíticas usam cache
cache-aside no Redis: a chave é derivada da rota e dos parâmetros, o TTL é
configurável, e o Airflow invalida as chaves ao fim de cada carga. O header
X-Cache (HIT/MISS) e /cache/stats tornam o efeito do cache observável.

Documentação interativa: http://localhost:8000/docs
"""
import functools
import hashlib
import json
import os
import time
from datetime import date, datetime, timezone
from typing import Optional

import redis
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.query import dict_factory
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse

from alert_rules import RULES

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "cassandra")
KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "airquality")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "600"))
SENSOR_ID = "airquality-uci-01"

app = FastAPI(title="Air Quality API", version="1.0.0",
              description="Consulta dos dados processados pelo pipeline Air Quality (Cassandra + cache Redis).")
_state = {"cluster": None, "session": None}
rds = redis.Redis(host=REDIS_HOST, decode_responses=True, socket_timeout=2)


def session():
    if _state["session"] is None:
        cluster = Cluster([CASSANDRA_HOST], protocol_version=5)
        s = cluster.connect(KEYSPACE)
        s.row_factory = dict_factory
        _state.update(cluster=cluster, session=s)
    return _state["session"]


def reset_session():
    if _state["cluster"] is not None:
        try:
            _state["cluster"].shutdown()
        except Exception:  # noqa: BLE001
            pass
    _state.update(cluster=None, session=None)


def rows(cql, params=None):
    """Executa a consulta; se o Cassandra reiniciou (outro IP), reconecta pelo hostname e tenta de novo."""
    try:
        return list(session().execute(cql, params or [], timeout=30))
    except NoHostAvailable:
        reset_session()
        return list(session().execute(cql, params or [], timeout=30))


def jsonable(v):
    if isinstance(v, datetime):
        return v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if hasattr(v, "date") and type(v).__name__ == "Date":  # cassandra.util.Date
        return str(v)
    return v


def clean(rs):
    return [{k: jsonable(v) for k, v in r.items()} for r in rs]


def cached(prefix):
    """Decorator cache-aside: tenta o Redis; em MISS executa a consulta e grava com TTL."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(request: Request, response: Response, *args, **kwargs):
            raw = f"{request.url.path}?{sorted(request.query_params.items())}"
            key = f"api:{prefix}:{hashlib.sha1(raw.encode()).hexdigest()[:16]}"
            try:
                hit = rds.get(key)
            except redis.RedisError:
                hit = None
            if hit is not None:
                rds.incr("stats:cache_hits")
                response.headers["X-Cache"] = "HIT"
                return json.loads(hit)
            t0 = time.perf_counter()
            data = fn(request, response, *args, **kwargs)
            try:
                rds.setex(key, CACHE_TTL, json.dumps(data, default=str))
                rds.incr("stats:cache_misses")
            except redis.RedisError:
                pass
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Query-Ms"] = f"{(time.perf_counter() - t0) * 1000:.1f}"
            return data
        return wrapper
    return deco


def parse_range(start: Optional[date], end: Optional[date]):
    meta = coverage()
    start = start or date.fromisoformat(meta["first_day"])
    end = end or date.fromisoformat(meta["last_day"])
    if start > end:
        raise HTTPException(400, "start deve ser <= end")
    return start, end


def coverage():
    years = sorted({r["year"] for r in rows("SELECT DISTINCT year FROM daily_summary")})
    if not years:
        raise HTTPException(503, "Sem dados: execute a DAG pipeline_airquality")
    first = rows("SELECT day FROM daily_summary WHERE year = %s ORDER BY day ASC LIMIT 1", [years[0]])[0]["day"]
    last = rows("SELECT day FROM daily_summary WHERE year = %s ORDER BY day DESC LIMIT 1", [years[-1]])[0]["day"]
    return {"years": years, "first_day": str(first), "last_day": str(last)}


def daily_rows(start, end):
    out = []
    for y in range(start.year, end.year + 1):
        out += rows("SELECT * FROM daily_summary WHERE year = %s AND day >= %s AND day <= %s", [y, start, end])
    return out


def months_between(start, end):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


# --------------------------------------------------------------------------- endpoints

@app.get("/", include_in_schema=False)
def root():
    """A raiz leva à documentação interativa (Swagger)."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["operação"])
def health():
    status = {}
    try:
        status["cassandra"] = rows("SELECT release_version FROM system.local")[0]["release_version"]
    except Exception as exc:  # noqa: BLE001
        status["cassandra"] = f"erro: {exc}"
    try:
        status["redis"] = "ok" if rds.ping() else "erro"
    except Exception as exc:  # noqa: BLE001
        status["redis"] = f"erro: {exc}"
    ok = not any(str(v).startswith("erro") for v in status.values())
    return {"status": "ok" if ok else "degraded", **status}


@app.get("/api/v1/meta", tags=["consulta"])
@cached("meta")
def meta(request: Request, response: Response):
    """Período coberto e definição das regras de alerta."""
    return {**coverage(), "sensor_id": SENSOR_ID, "alert_rules": RULES}


@app.get("/api/v1/summary", tags=["consulta"])
@cached("summary")
def summary(request: Request, response: Response, start: Optional[date] = None, end: Optional[date] = None):
    """KPIs do período: registros, temperatura média, CO/NO2 médios e máximos, alertas."""
    start, end = parse_range(start, end)
    d = daily_rows(start, end)
    if not d:
        raise HTTPException(404, "Nenhum dado no período")
    n = sum(r["readings"] for r in d)

    def wavg(col):
        pairs = [(r[col], r["readings"]) for r in d if r[col] is not None]
        w = sum(p[1] for p in pairs)
        return round(sum(v * c for v, c in pairs) / w, 2) if w else None

    return {
        "start": str(start), "end": str(end), "days": len(d), "readings": n,
        "temperature_avg_c": wavg("temp_avg"), "co_avg_mg_m3": wavg("co_avg"), "no2_avg_ug_m3": wavg("no2_avg"),
        "co_max_mg_m3": max((r["co_max"] for r in d if r["co_max"] is not None), default=None),
        "no2_max_ug_m3": max((r["no2_max"] for r in d if r["no2_max"] is not None), default=None),
        "alerts": sum(r["alerts"] for r in d),
        "completeness_avg_pct": wavg("completeness_pct"),
    }


@app.get("/api/v1/daily", tags=["consulta"])
@cached("daily")
def daily(request: Request, response: Response, start: Optional[date] = None, end: Optional[date] = None):
    """Série diária (tabela daily_summary)."""
    start, end = parse_range(start, end)
    return clean(daily_rows(start, end))


@app.get("/api/v1/readings/{day}", tags=["consulta"])
@cached("readings")
def readings(request: Request, response: Response, day: date):
    """Leituras horárias de um dia (tabela readings_by_day, uma partição)."""
    r = rows("SELECT * FROM readings_by_day WHERE day = %s", [day])
    if not r:
        raise HTTPException(404, f"Sem leituras em {day}")
    return clean(r)


@app.get("/api/v1/profile/hourly", tags=["consulta"])
@cached("profile")
def hourly_profile(request: Request, response: Response,
                   profile: str = Query("all", pattern="^(all|weekday|weekend)$")):
    """Perfil médio por hora do dia (todos os dias, dias úteis ou fim de semana)."""
    return clean(rows("SELECT * FROM hourly_profile WHERE profile = %s", [profile]))


@app.get("/api/v1/alerts", tags=["consulta"])
@cached("alerts")
def alerts(request: Request, response: Response, start: Optional[date] = None, end: Optional[date] = None,
           rule: Optional[str] = None, limit: int = Query(500, ge=1, le=5000)):
    """Alertas do período (tabela alerts_by_month), mais recentes primeiro."""
    start, end = parse_range(start, end)
    out = []
    for month in reversed(list(months_between(start, end))):
        for r in rows("SELECT * FROM alerts_by_month WHERE month = %s", [month]):
            if start <= r["event_ts"].date() <= end and (rule is None or r["rule"] == rule):
                out.append(r)
        if len(out) >= limit:
            break
    return clean(out[:limit])


@app.get("/api/v1/latest", tags=["tempo real"])
def latest(response: Response, limit: int = Query(30, ge=1, le=500)):
    """Últimas leituras recebidas pelo streaming (sem cache: visão ao vivo)."""
    response.headers["X-Cache"] = "BYPASS"
    return clean(rows("SELECT * FROM latest_readings WHERE sensor_id = %s LIMIT %s", [SENSOR_ID, limit]))


@app.get("/api/v1/stream/status", tags=["tempo real"])
def stream_status():
    """Status do último micro-lote do Spark Structured Streaming (gravado no Redis)."""
    status = rds.get("stream:status")
    return {"last_batch": json.loads(status) if status else None,
            "rows_total": int(rds.get("stream:rows_total") or 0),
            "alerts_total": int(rds.get("stream:alerts_total") or 0)}


@app.get("/api/v1/pipeline/runs", tags=["operação"])
def pipeline_runs(limit: int = Query(10, ge=1, le=100)):
    """Histórico das execuções da DAG (tabela pipeline_runs)."""
    r = rows("SELECT * FROM pipeline_runs WHERE pipeline = 'pipeline_airquality' LIMIT %s", [limit])
    for x in r:
        x["details"] = json.loads(x["details"]) if x.get("details") else None
    return clean(r)


@app.get("/cache/stats", tags=["operação"])
def cache_stats():
    hits = int(rds.get("stats:cache_hits") or 0)
    misses = int(rds.get("stats:cache_misses") or 0)
    return {"hits": hits, "misses": misses,
            "hit_ratio": round(hits / (hits + misses), 3) if hits + misses else None,
            "keys": sum(1 for _ in rds.scan_iter("api:*")), "ttl_seconds": CACHE_TTL}
