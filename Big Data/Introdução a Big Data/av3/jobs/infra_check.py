"""Valida a comunicação entre os contêineres na rede mybridge.

Para cada serviço: resolve o nome DNS na rede Docker, abre uma conexão TCP e,
quando há protocolo de aplicação simples, faz uma chamada real (health do
MinIO, metadados do Kafka, UI do Spark Master, Cassandra, Redis e API).

Uso: python infra_check.py   (sai com código 1 se algum serviço falhar)
"""
import json
import socket
import sys
import time
import urllib.request

import settings

SERVICES = [
    ("minio", 9000, "MinIO API S3"),
    ("kafka1", 9092, "Kafka broker"),
    ("spark-master", 7077, "Spark Master (RPC)"),
    ("spark-master", 8080, "Spark Master (UI)"),
    ("spark-worker", 8081, "Spark Worker (UI)"),
    ("cassandra", 9042, "Cassandra (CQL)"),
    ("redis", 6379, "Redis"),
    ("api", 8000, "API FastAPI"),
    ("postgres", 5432, "Postgres (metadados Airflow)"),
]
# Interfaces de usuário: a ausência gera aviso, mas não impede o pipeline de rodar.
OPTIONAL = [
    ("dashboard", 8501, "Dashboard Streamlit"),
    ("airflow-webserver", 8080, "Airflow Webserver"),
]


def tcp_check(host, port, timeout=3.0):
    ip = socket.gethostbyname(host)
    t0 = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout):
        pass
    return ip, (time.perf_counter() - t0) * 1000


def app_checks():
    out = {}
    with urllib.request.urlopen(f"{settings.MINIO_ENDPOINT}/minio/health/live", timeout=5) as r:
        out["minio_health"] = r.status

    from confluent_kafka.admin import AdminClient

    md = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP}).list_topics(timeout=10)
    out["kafka_brokers"] = [f"{b.host}:{b.port}" for b in md.brokers.values()]

    with urllib.request.urlopen("http://spark-master:8080/json/", timeout=5) as r:
        info = json.loads(r.read())
    out["spark_status"] = info.get("status")
    out["spark_alive_workers"] = info.get("aliveworkers")
    out["spark_cores"] = info.get("cores")

    import cassandra_admin

    cluster, session = cassandra_admin.connect(retries=3, wait=2)
    try:
        out["cassandra_version"] = session.execute("SELECT release_version FROM system.local").one().release_version
    finally:
        cluster.shutdown()

    import redis

    out["redis_ping"] = redis.Redis(host=settings.REDIS_HOST, socket_timeout=3).ping()

    with urllib.request.urlopen(f"{settings.API_URL}/health", timeout=10) as r:
        out["api_health"] = json.loads(r.read()).get("status")
    return out


def run():
    print(f"Host atual: {socket.gethostname()} ({socket.gethostbyname(socket.gethostname())})")
    print(f"{'serviço':32} {'host:porta':26} {'IP mybridge':15} {'latência':>9}  status")
    failures = []
    for host, port, label in SERVICES + OPTIONAL:
        required = (host, port, label) in SERVICES
        try:
            ip, ms = tcp_check(host, port)
            print(f"{label:32} {host + ':' + str(port):26} {ip:15} {ms:7.1f}ms  OK")
        except Exception as exc:  # noqa: BLE001 - queremos reportar qualquer falha
            tag = "FALHA" if required else "AVISO (opcional)"
            print(f"{label:32} {host + ':' + str(port):26} {'-':15} {'-':>9}  {tag} ({exc})")
            if required:
                failures.append(label)

    apps = app_checks()
    print("Checagens de aplicação:", json.dumps(apps, ensure_ascii=False))
    if apps.get("spark_alive_workers", 0) < 1:
        failures.append("Spark sem workers ativos")
    if failures:
        raise RuntimeError(f"Serviços indisponíveis: {failures}")
    print("Todos os serviços estão acessíveis pela rede mybridge.")
    return apps


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        sys.exit(1)
