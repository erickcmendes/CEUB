"""Conexão e criação idempotente do schema do Cassandra (cassandra/schema.cql)."""
import re
import time

import settings


def connect(retries=30, wait=5):
    from cassandra.cluster import Cluster

    last = None
    for _ in range(retries):
        try:
            cluster = Cluster([settings.CASSANDRA_HOST], protocol_version=5)
            return cluster, cluster.connect()
        except Exception as exc:  # noqa: BLE001 - Cassandra demora a aceitar conexões no boot
            last = exc
            time.sleep(wait)
    raise RuntimeError(f"Cassandra indisponível: {last}")


def ensure_schema(path=None):
    path = path or settings.CASSANDRA_SCHEMA_FILE
    with open(path, encoding="utf-8") as fh:
        cql = re.sub(r"--[^\n]*", "", fh.read())
    statements = [s.strip() for s in cql.split(";") if s.strip()]
    cluster, session = connect()
    try:
        for stmt in statements:
            session.execute(stmt, timeout=60)
        rows = session.execute(
            "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", [settings.CASSANDRA_KEYSPACE]
        )
        tables = sorted(r.table_name for r in rows)
        version = session.execute("SELECT release_version FROM system.local").one().release_version
        print(f"Cassandra {version}: keyspace '{settings.CASSANDRA_KEYSPACE}' com {len(tables)} tabelas: {tables}")
        return {"cassandra_version": version, "tables": tables, "statements": len(statements)}
    finally:
        cluster.shutdown()


if __name__ == "__main__":
    ensure_schema()
