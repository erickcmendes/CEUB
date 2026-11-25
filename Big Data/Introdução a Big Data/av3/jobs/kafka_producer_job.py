"""Producer: lê o CSV de origem no MinIO e publica cada linha como JSON no Kafka.

Decisões:
- Os valores são publicados como texto, exatamente como estão no CSV
  (vírgula decimal, -200 para ausente). Tratamento e tipagem são papel do Spark.
- Só os nomes das colunas são normalizados (ex.: "PT08.S1(CO)" -> "pt08_s1_co"),
  para gerar chaves JSON seguras.
- Linhas totalmente vazias (o arquivo da UCI tem ~114 no final) são descartadas
  e contadas.
- Chave da mensagem = "data hora": leituras do mesmo instante caem na mesma
  partição.
- acks=all + idempotência: sem duplicatas causadas por reenvio.
- Os offsets (início/fim por partição) desta execução são devolvidos, e o Spark
  processa exatamente essa fatia do tópico. Isso deixa as reexecuções
  determinísticas.
"""
import csv
import io
import json
import re
import sys
import time
from datetime import datetime, timezone

from confluent_kafka import Consumer, Producer, TopicPartition

import settings


def normalize(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", name.strip().lower()).strip("_")


def read_source_from_minio():
    s3 = settings.s3_client()
    obj = s3.get_object(Bucket=settings.BUCKET, Key=settings.SOURCE_KEY)
    raw = obj["Body"].read()
    print(f"Lido s3://{settings.BUCKET}/{settings.SOURCE_KEY}: {len(raw)} bytes")
    return raw.decode("utf-8-sig")


def watermarks(topic):
    """Retorna {partição: high watermark} do tópico."""
    c = Consumer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP, "group.id": "av3-offset-probe",
                  "enable.auto.commit": False})
    try:
        md = c.list_topics(topic, timeout=10)
        if topic not in md.topics or md.topics[topic].error:
            raise RuntimeError(f"Tópico '{topic}' não existe. Rode a tarefa create_kafka_topic antes.")
        out = {}
        for p in sorted(md.topics[topic].partitions):
            _low, high = c.get_watermark_offsets(TopicPartition(topic, p), timeout=10)
            out[p] = high
        return out
    finally:
        c.close()


def produce(run_id: str = None, topic: str = None):
    topic = topic or settings.KAFKA_TOPIC
    run_id = run_id or datetime.now(timezone.utc).strftime("manual__%Y%m%dT%H%M%S")
    text = read_source_from_minio()

    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader)
    cols = [(i, normalize(h)) for i, h in enumerate(header) if h.strip()]
    print(f"Colunas de origem ({len(cols)}): {[c for _, c in cols]}")

    start = watermarks(topic)

    stats = {"lines_read": 0, "blank_skipped": 0, "sent": 0, "delivered": 0, "errors": 0}

    def on_delivery(err, _msg):
        if err is not None:
            stats["errors"] += 1
            print(f"Falha de entrega: {err}", file=sys.stderr)
        else:
            stats["delivered"] += 1

    producer = Producer({
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP,
        "acks": "all",
        "enable.idempotence": True,
        "linger.ms": 20,
        "batch.num.messages": 1000,
        "client.id": "av3-airquality-producer",
    })

    t0 = time.perf_counter()
    ingested_at = datetime.now(timezone.utc).isoformat()
    for line_no, row in enumerate(reader, start=2):  # linha 1 = cabeçalho
        stats["lines_read"] += 1
        if not any(cell.strip() for cell in row):
            stats["blank_skipped"] += 1
            continue
        payload = {name: (row[i].strip() if i < len(row) else None) for i, name in cols}
        message = {
            "run_id": run_id,
            "source": f"s3://{settings.BUCKET}/{settings.SOURCE_KEY}",
            "source_line": line_no,
            "ingested_at": ingested_at,
            "payload": payload,
        }
        key = f"{payload.get('date')} {payload.get('time')}"
        producer.produce(topic, key=key.encode(), value=json.dumps(message).encode(),
                         on_delivery=on_delivery)
        stats["sent"] += 1
        producer.poll(0)
        if stats["sent"] % 2000 == 0:
            print(f"  {stats['sent']} mensagens enviadas...")
            if stats["sent"] == 2000:
                print(f"  exemplo de mensagem: {json.dumps(message, ensure_ascii=False)}")

    remaining = producer.flush(60)
    elapsed = time.perf_counter() - t0
    if remaining or stats["errors"] or stats["delivered"] != stats["sent"]:
        raise RuntimeError(f"Entrega incompleta: {stats}, pendentes={remaining}")

    end = watermarks(topic)
    produced_by_offsets = sum(end[p] - start.get(p, 0) for p in end)
    if produced_by_offsets != stats["delivered"]:
        # Outro producer escrevendo ao mesmo tempo invalidaria a fatia de offsets.
        raise RuntimeError(f"Offsets ({produced_by_offsets}) != mensagens entregues ({stats['delivered']})")

    result = {
        "run_id": run_id,
        "topic": topic,
        **stats,
        "seconds": round(elapsed, 2),
        "msgs_per_sec": round(stats["delivered"] / elapsed, 1) if elapsed else None,
        # formato aceito por startingOffsets/endingOffsets do Spark
        "starting_offsets": json.dumps({topic: {str(p): o for p, o in start.items()}}),
        "ending_offsets": json.dumps({topic: {str(p): o for p, o in end.items()}}),
    }
    print("Resumo da ingestão:", json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    produce(sys.argv[1] if len(sys.argv) > 1 else None)
