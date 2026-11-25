"""Configuração centralizada do pipeline, lida de variáveis de ambiente (.env)."""
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET = os.getenv("MINIO_BUCKET", "air-quality")
SOURCE_KEY = os.getenv("SOURCE_KEY", "raw/airquality.csv")
REPORTS_PREFIX = os.getenv("REPORTS_PREFIX", "reports")

# Lakehouse (Delta Lake) no MinIO
LAKEHOUSE = f"s3a://{BUCKET}/lakehouse"
BRONZE_PATH = f"{LAKEHOUSE}/bronze/sensor_raw"
SILVER_PATH = f"{LAKEHOUSE}/silver/airquality"
GOLD_DAILY_PATH = f"{LAKEHOUSE}/gold/daily_summary"
GOLD_HOURLY_PATH = f"{LAKEHOUSE}/gold/hourly_profile"
GOLD_ALERTS_PATH = f"{LAKEHOUSE}/gold/alerts"
STREAM_CHECKPOINT = f"s3a://{BUCKET}/checkpoints/stream_serving"

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka1:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor_raw")
KAFKA_PARTITIONS = int(os.getenv("KAFKA_PARTITIONS", "3"))
KAFKA_ALERTS_TOPIC = os.getenv("KAFKA_ALERTS_TOPIC", "sensor_alerts")

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "cassandra")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "airquality")
CASSANDRA_SCHEMA_FILE = os.getenv("CASSANDRA_SCHEMA_FILE", "/opt/airflow/cassandra/schema.cql")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
API_URL = os.getenv("API_URL", "http://api:8000")

SENSOR_ID = "airquality-uci-01"

# CSV local montado no contêiner do Airflow; é enviado ao MinIO pela DAG.
LOCAL_SOURCE_CSV = os.getenv("LOCAL_SOURCE_CSV", "/opt/airflow/data/airquality.csv")


def s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def delta_storage_options():
    """Opções para ler as tabelas Delta com a biblioteca deltalake (delta-rs), sem Spark."""
    return {
        "AWS_ENDPOINT_URL": MINIO_ENDPOINT,
        "AWS_ACCESS_KEY_ID": MINIO_ACCESS_KEY,
        "AWS_SECRET_ACCESS_KEY": MINIO_SECRET_KEY,
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }


def to_s3_uri(s3a_path):
    return s3a_path.replace("s3a://", "s3://", 1)
