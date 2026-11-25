#!/usr/bin/env bash
# Coleta evidências reais de uma execução da DAG em evidencias/etapa3/.
# Uso: ./scripts/collect_evidence.sh <run_id>
set -euo pipefail
cd "$(dirname "$0")/.."
RUN="${1:?informe o run_id da DAG}"
OUT=evidencias/etapa3
LOGDIR="logs/dag_id=pipeline_airquality/run_id=$RUN"
mkdir -p "$OUT/dag_logs"

echo "==> Contêineres e rede"
{
  echo "===== docker compose ps"; docker compose --profile streaming ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
  echo; echo "===== Rede mybridge"; docker network inspect mybridge --format '{{range .Containers}}{{printf "%-22s %s\n" .Name .IPv4Address}}{{end}}' | sort
  echo; echo "===== Comunicação (a partir do airflow-scheduler)"; docker exec airflow-scheduler python /opt/airflow/jobs/infra_check.py
  echo; echo "===== Uso de recursos"; docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
} > "$OUT/01_ambiente_rede.txt" 2>&1

echo "==> Logs das tarefas da DAG ($RUN)"
for d in "$LOGDIR"/task_id=*; do
  t=${d##*task_id=}; f=$(ls -t "$d"/attempt=*.log | head -1)
  cp "$f" "$OUT/dag_logs/${t}.log"
done
docker exec airflow-scheduler airflow tasks states-for-dag-run pipeline_airquality "$RUN" -o table \
  > "$OUT/02_dag_estados.txt" 2>/dev/null
docker exec airflow-scheduler airflow dags list-runs -d pipeline_airquality -o table \
  > "$OUT/02_dag_historico_execucoes.txt" 2>/dev/null

echo "==> Kafka"
{
  for t in sensor_raw sensor_alerts; do
    docker exec kafka1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka1:9092 --describe --topic $t
    docker exec kafka1 /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server kafka1:9092 --topic $t
    echo
  done
  echo "===== Exemplos de alertas em sensor_alerts"
  docker exec kafka1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka1:9092 \
    --topic sensor_alerts --from-beginning --max-messages 5 2>/dev/null
} > "$OUT/03_kafka.txt" 2>&1

echo "==> MinIO (lakehouse e relatórios)"
{
  docker exec minio mc alias set l http://localhost:9000 "$(grep ^MINIO_ROOT_USER .env | cut -d= -f2)" \
    "$(grep ^MINIO_ROOT_PASSWORD .env | cut -d= -f2)" >/dev/null
  docker exec minio mc du --depth 3 l/air-quality
  echo; docker exec minio mc ls --recursive "l/air-quality/lakehouse/silver/airquality/_delta_log/"
  echo; docker exec minio mc ls --recursive "l/air-quality/reports/run_id=$RUN/"
} > "$OUT/04_minio_lakehouse.txt" 2>&1
for s in bronze silver gold serving validation run_summary; do
  docker exec minio mc cat "l/air-quality/reports/run_id=$RUN/$s.json" > "$OUT/report_${s}.json" 2>/dev/null || true
done

echo "==> Cassandra"
{
  docker exec cassandra cqlsh -e "DESCRIBE KEYSPACE airquality" | head -40
  for t in readings_by_day daily_summary hourly_profile alerts_by_month latest_readings pipeline_runs; do
    echo "--- $t"; docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM airquality.$t"
  done
  docker exec cassandra cqlsh -e "SELECT day, readings, co_avg, no2_max, alerts FROM airquality.daily_summary WHERE year=2004 AND day >= '2004-11-15' AND day <= '2004-11-20'"
  docker exec cassandra cqlsh -e "SELECT started_at, run_id, status, duration_s, rows_inserted, rows_updated, alerts, checks_passed, checks_total FROM airquality.pipeline_runs WHERE pipeline='pipeline_airquality' LIMIT 5"
} > "$OUT/05_cassandra.txt" 2>&1

echo "==> API e cache Redis"
{
  for ep in /health "/api/v1/summary" "/api/v1/summary?start=2004-11-01&end=2004-11-30" "/api/v1/profile/hourly?profile=weekday" \
            "/api/v1/alerts?start=2005-02-01&end=2005-02-28&limit=5" "/api/v1/readings/2004-11-17" /api/v1/pipeline/runs?limit=3 /cache/stats; do
    for i in 1 2; do
      echo "### GET $ep  (chamada $i)"
      curl -s -D - "localhost:8000$ep" -o /tmp/av3_body.json | grep -iE '^(HTTP|x-cache|x-query-ms)'
      python3 -c "import json;d=json.load(open('/tmp/av3_body.json'));print(json.dumps(d if not isinstance(d,list) else {'itens':len(d),'primeiros':d[:2]},ensure_ascii=False,indent=1)[:900])"
      echo
      [ "$ep" = /health ] || [ "$ep" = /cache/stats ] || [[ "$ep" == *pipeline* ]] && break
    done
  done
} > "$OUT/06_api_cache.txt" 2>&1
rm -f /tmp/av3_body.json

echo "Evidências salvas em $OUT/"
ls -la "$OUT"
