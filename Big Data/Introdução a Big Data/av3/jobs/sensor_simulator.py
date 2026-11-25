"""Simulador de sensor: reproduz o dataset no Kafka como um fluxo contínuo.

Lê o CSV de origem no MinIO e publica uma leitura a cada 1/rate segundos no
tópico sensor_raw, no mesmo formato JSON do Producer em lote. Ao chegar ao fim
do arquivo, recomeça do início. Representa o sensor de campo e alimenta o job
de streaming.

Uso: python sensor_simulator.py --rate 2 --start-line 2000
"""
import argparse
import csv
import io
import json
import time
from datetime import datetime, timezone

from confluent_kafka import Producer

import settings
from kafka_producer_job import normalize, read_source_from_minio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.0, help="leituras por segundo")
    ap.add_argument("--start-line", type=int, default=2)
    args = ap.parse_args()

    for attempt in range(60):  # aguarda o CSV existir no MinIO (a DAG o publica)
        try:
            text = read_source_from_minio()
            break
        except Exception as exc:  # noqa: BLE001
            print(f"Aguardando s3://{settings.BUCKET}/{settings.SOURCE_KEY}: {exc}")
            time.sleep(10)
    else:
        raise SystemExit("CSV de origem não encontrado")

    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader)
    cols = [(i, normalize(h)) for i, h in enumerate(header) if h.strip()]
    rows = [(n, r) for n, r in enumerate(reader, start=2) if any(c.strip() for c in r)]
    producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP, "acks": "all",
                         "enable.idempotence": True, "client.id": "av3-sensor-simulator"})
    idx = next((i for i, (n, _) in enumerate(rows) if n >= args.start_line), 0)
    print(f"Simulador iniciado: {len(rows)} leituras, {args.rate}/s, a partir da linha {rows[idx][0]}")

    sent = 0
    while True:
        line_no, row = rows[idx]
        payload = {name: (row[i].strip() if i < len(row) else None) for i, name in cols}
        msg = {"run_id": "stream-simulator", "source": "sensor-simulator", "source_line": line_no,
               "ingested_at": datetime.now(timezone.utc).isoformat(), "payload": payload}
        producer.produce(settings.KAFKA_TOPIC, key=f"{payload['date']} {payload['time']}".encode(),
                         value=json.dumps(msg).encode())
        producer.poll(0)
        sent += 1
        if sent % 50 == 0:
            producer.flush(10)
            print(f"{sent} leituras enviadas (última: {payload['date']} {payload['time']}, "
                  f"CO={payload['co_gt']}, NO2={payload['no2_gt']})", flush=True)
        idx = (idx + 1) % len(rows)
        time.sleep(1.0 / args.rate)


if __name__ == "__main__":
    main()
