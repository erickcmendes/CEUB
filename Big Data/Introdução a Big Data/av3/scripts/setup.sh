#!/usr/bin/env bash
# Prepara e sobe o ambiente da AV3 de forma idempotente.
#   1. cria a rede Docker externa "mybridge" (se não existir)
#   2. gera o .env (UID do Airflow + chave Fernet) a partir de .env.example
#   3. baixa o dataset Air Quality (UCI) para data/airquality.csv
#   4. builda a imagem do Airflow e sobe todos os serviços
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Rede mybridge"
docker network inspect mybridge >/dev/null 2>&1 || docker network create --driver bridge mybridge
docker network inspect mybridge --format '    {{.Name}} driver={{.Driver}} subnet={{(index .IPAM.Config 0).Subnet}}'

echo "==> Arquivo .env"
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s|^AIRFLOW_UID=.*|AIRFLOW_UID=$(id -u)|" .env
  FERNET=$(python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
  sed -i "s|^AIRFLOW__CORE__FERNET_KEY=.*|AIRFLOW__CORE__FERNET_KEY=${FERNET}|" .env
  echo "    .env criado (AIRFLOW_UID=$(id -u), chave Fernet gerada)"
else
  echo "    .env já existe, mantido"
fi

echo "==> Dataset"
mkdir -p data logs
if [ ! -s data/airquality.csv ]; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/aq.zip" https://archive.ics.uci.edu/static/public/360/air+quality.zip
  unzip -o -q "$tmp/aq.zip" AirQualityUCI.csv -d "$tmp"
  mv "$tmp/AirQualityUCI.csv" data/airquality.csv
  rm -rf "$tmp"
fi
echo "    data/airquality.csv: $(wc -l < data/airquality.csv) linhas, $(du -h data/airquality.csv | cut -f1)"

echo "==> Build e subida dos contêineres"
docker compose build
docker compose up -d

echo "==> Aguardando serviços ficarem saudáveis"
for i in $(seq 1 60); do
  unhealthy=$(docker compose ps --format '{{.Service}} {{.Health}}' | awk '$2!="" && $2!="healthy"{print $1}')
  [ -z "$unhealthy" ] && break
  sleep 5
done
docker compose ps
echo
echo "Airflow:        http://localhost:8080  (admin/admin)"
echo "Dashboard:      http://localhost:8501"
echo "API (Swagger):  http://localhost:8000/docs"
echo "MinIO console:  http://localhost:9001  (minioadmin/minioadmin)"
echo "Spark Master:   http://localhost:8081"
echo
echo "Executar o pipeline:  docker exec airflow-scheduler airflow dags trigger pipeline_airquality"
echo "Streaming:            ./scripts/streaming_demo.sh"
