# Evidências da etapa 2 (escopo mínimo)

Primeira versão do pipeline, executada em 2026-11-25 (run `manual__av3_20261125T121440`):
MinIO (CSV) → Kafka (JSON) → Spark → MinIO (Parquet em `processed/airquality/`), com validação via PyArrow.

- `01_rede_mybridge.txt`: comunicação entre os contêineres (item 2a)
- `dag_*.log`: logs de cada tarefa da DAG nessa versão
- `kafka_topico.txt`, `minio_bucket.txt`: tópico e objetos gerados
- `codigo_etapa2/`: o job Spark e a validação dessa versão

Na etapa 3, esses dois jobs foram substituídos pelas camadas Bronze, Silver e Gold em Delta Lake
(`jobs/bronze_ingest_job.py`, `jobs/silver_transform_job.py`, `jobs/gold_aggregate_job.py`) e pela
validação cruzada `jobs/validate_pipeline.py`. O Parquet da etapa 2 continua no MinIO, em `air-quality/processed/`.
