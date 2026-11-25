#!/usr/bin/env bash
# Evidência do item 2a: contêineres na rede mybridge e comunicação entre eles.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "===== docker compose ps"
docker compose ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

echo
echo "===== Contêineres conectados à rede mybridge"
docker network inspect mybridge \
  --format '{{range .Containers}}{{printf "%-22s %s\n" .Name .IPv4Address}}{{end}}' | sort

echo
echo "===== Testes de comunicação a partir do airflow-scheduler"
docker exec airflow-scheduler python /opt/airflow/jobs/infra_check.py

echo
echo "===== Spark worker -> Kafka e MinIO (conectividade a partir de outro contêiner)"
docker exec spark-worker bash -c '
  for hp in kafka1:9092 minio:9000 spark-master:7077; do
    h=${hp%:*}; p=${hp#*:}
    if timeout 3 bash -c "</dev/tcp/$h/$p" 2>/dev/null; then echo "spark-worker -> $hp OK"; else echo "spark-worker -> $hp FALHA"; exit 1; fi
  done'
