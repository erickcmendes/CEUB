"""Cria os tópicos Kafka de forma idempotente.

- sensor_raw:    leituras brutas em JSON (3 partições)
- sensor_alerts: alertas de qualidade do ar publicados pelo Spark (lote e streaming)

O broker está com auto.create.topics.enable=false, então o pipeline só
funciona se esta etapa rodar antes do Producer.
"""
from confluent_kafka.admin import AdminClient, NewTopic

import settings

TOPICS = {
    settings.KAFKA_TOPIC: {"partitions": settings.KAFKA_PARTITIONS, "retention.ms": str(7 * 24 * 3600 * 1000)},
    settings.KAFKA_ALERTS_TOPIC: {"partitions": 1, "retention.ms": str(30 * 24 * 3600 * 1000)},
}


def create_topics():
    admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP})
    existing = admin.list_topics(timeout=10).topics
    result = {}
    new = []
    for topic, cfg in TOPICS.items():
        if topic in existing:
            result[topic] = {"partitions": len(existing[topic].partitions), "created": False}
            print(f"Tópico '{topic}' já existe com {result[topic]['partitions']} partição(ões).")
        else:
            new.append(NewTopic(topic, num_partitions=cfg["partitions"], replication_factor=1,
                                config={"retention.ms": cfg["retention.ms"]}))
    if new:
        for topic, fut in admin.create_topics(new).items():
            fut.result()  # levanta exceção se a criação falhar
            n = len(admin.list_topics(topic=topic, timeout=10).topics[topic].partitions)
            result[topic] = {"partitions": n, "created": True}
            print(f"Tópico '{topic}' criado com {n} partição(ões).")
    return result


if __name__ == "__main__":
    create_topics()
