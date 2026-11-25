#!/usr/bin/env bash
# Demonstração do processamento contínuo:
#   simulador de sensor -> Kafka -> Spark Structured Streaming -> Cassandra + Kafka (alertas)
# Uso: ./scripts/streaming_demo.sh [segundos]   (padrão: 120)
set -euo pipefail
cd "$(dirname "$0")/.."
DUR="${1:-120}"

echo "==> Subindo perfil streaming (spark-streaming + sensor-simulator)"
docker compose --profile streaming up -d spark-streaming sensor-simulator

echo "==> Aguardando o streaming processar por ${DUR}s"
sleep "$DUR"

echo
echo "===== Spark Master: aplicações ativas"
docker exec airflow-scheduler python -c "
import json, urllib.request
d = json.load(urllib.request.urlopen('http://spark-master:8080/json/'))
for a in d['activeapps']:
    print(f\"{a['id']}  {a['name']:28} cores={a['cores']} mem={a['memoryperslave']}MB estado={a['state']}\")
"

echo
echo "===== Log do simulador (últimas linhas)"
docker logs sensor-simulator 2>&1 | tail -5

echo
echo "===== Log do Spark Streaming (micro-lotes)"
docker logs spark-streaming 2>&1 | grep -E 'micro-lote|Streaming iniciado' | tail -10

echo
echo "===== Status do streaming na API (Redis)"
curl -s localhost:8000/api/v1/stream/status; echo

echo
echo "===== Últimas leituras no Cassandra (via API /api/v1/latest)"
curl -s "localhost:8000/api/v1/latest?limit=5" | python3 -c "
import json, sys
for r in json.load(sys.stdin):
    print(r['received_at'][:19], '| evento', r['event_ts'][:19], '| CO', r['co_mg_m3'], '| NO2', r['no2_ug_m3'], '| alertas:', r['alert_rules'] or '-')
"

echo
echo "===== Alertas no tópico Kafka sensor_alerts (últimos 5 do streaming)"
docker exec kafka1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka1:9092 \
  --topic sensor_alerts --from-beginning --timeout-ms 8000 2>/dev/null | grep '"source":"stream"' | tail -5 || true
