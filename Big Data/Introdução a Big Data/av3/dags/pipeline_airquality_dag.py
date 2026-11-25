"""DAG do pipeline Air Quality: Lakehouse (Delta) + serving no Cassandra (AV3 - Big Data / CEUB).

```
check_infra ─> preparacao[upload_source_to_minio | create_kafka_topics | prepare_cassandra_schema]
            ─> produce_to_kafka
            ─> lakehouse[bronze_ingest ─> silver_transform ─> gold_aggregate]
            ─> serving[load_cassandra ─> validate_pipeline ─> refresh_api_cache]
            ─> record_run (all_done)
```

- **check_infra**: DNS/TCP/saúde de todos os serviços na rede mybridge
- **preparacao**: CSV de origem no MinIO, tópicos Kafka, schema do Cassandra (tudo idempotente)
- **produce_to_kafka**: Producer Python lê o CSV do MinIO e publica JSON em `sensor_raw`
- **lakehouse**: jobs Spark no cluster Standalone; Bronze (bruto) -> Silver (tratado, MERGE)
  -> Gold (agregados + alertas, publicados em `sensor_alerts`)
- **serving**: Spark carrega Silver/Gold no Cassandra; validação independente (deltalake +
  driver Cassandra); invalidação e pré-aquecimento do cache Redis da API
- **record_run**: grava status, duração e métricas em `airquality.pipeline_runs`

Agendada diariamente. Reexecutar com os mesmos dados não duplica nada: a Bronze guarda o
histórico de cargas, e a Silver só altera linhas cujos valores mudaram.
"""
import glob
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

JOBS = "/opt/airflow/jobs"
SPARK_JARS = ",".join(sorted(glob.glob("/opt/spark-jars/*.jar")))
SPARK_CONF = {
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.memory": "512m",
    "spark.executor.memory": "512m",
    "spark.executor.cores": "2",
    "spark.cores.max": "2",
    "spark.sql.shuffle.partitions": "4",
    "spark.default.parallelism": "4",
}


def spark_task(task_id, script, extra_args=(), **kwargs):
    return SparkSubmitOperator(
        task_id=task_id,
        conn_id="spark_default",
        application=f"{JOBS}/{script}",
        name=f"av3-{task_id}-{{{{ ts_nodash }}}}",
        jars=SPARK_JARS,
        application_args=["--run-id", "{{ run_id }}", *extra_args],
        conf=SPARK_CONF,
        verbose=False,
        execution_timeout=timedelta(minutes=20),
        **kwargs,
    )


def _check_infra():
    import infra_check
    return infra_check.run()


def _upload_source():
    import minio_source
    return minio_source.upload_source()


def _create_topics():
    import kafka_topic
    return kafka_topic.create_topics()


def _prepare_cassandra():
    import cassandra_admin
    return cassandra_admin.ensure_schema()


def _produce(run_id, **_):
    import kafka_producer_job
    return kafka_producer_job.produce(run_id=run_id)


def _validate(run_id, ti, **_):
    import validate_pipeline
    produced = ti.xcom_pull(task_ids="produce_to_kafka")["delivered"]
    return validate_pipeline.validate(run_id=run_id, produced=produced)


def _refresh_cache():
    import ops_tasks
    return ops_tasks.refresh_api_cache()


def _record_run(**context):
    import ops_tasks
    return ops_tasks.record_run(**context)


default_args = {
    "owner": "av3",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=30),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="pipeline_airquality",
    description="MinIO -> Kafka -> Spark (Delta Bronze/Silver/Gold) -> Cassandra -> API/Dashboard",
    default_args=default_args,
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=1),
    tags=["av3", "airquality", "kafka", "spark", "delta", "cassandra"],
    doc_md=__doc__,
) as dag:

    check_infra = PythonOperator(task_id="check_infra", python_callable=_check_infra, retries=5)

    with TaskGroup("preparacao") as preparacao:
        PythonOperator(task_id="upload_source_to_minio", python_callable=_upload_source)
        PythonOperator(task_id="create_kafka_topics", python_callable=_create_topics)
        PythonOperator(task_id="prepare_cassandra_schema", python_callable=_prepare_cassandra)

    produce = PythonOperator(
        task_id="produce_to_kafka",
        python_callable=_produce,
        op_kwargs={"run_id": "{{ run_id }}"},
        retries=0,  # reenviar geraria uma nova fatia de offsets; a Bronze já é idempotente por run
    )

    with TaskGroup("lakehouse") as lakehouse:
        bronze = spark_task(
            "bronze_ingest", "bronze_ingest_job.py",
            ["--starting-offsets", "{{ ti.xcom_pull(task_ids='produce_to_kafka')['starting_offsets'] }}",
             "--ending-offsets", "{{ ti.xcom_pull(task_ids='produce_to_kafka')['ending_offsets'] }}"],
        )
        silver = spark_task("silver_transform", "silver_transform_job.py")
        gold = spark_task("gold_aggregate", "gold_aggregate_job.py")
        bronze >> silver >> gold

    with TaskGroup("serving") as serving:
        load = spark_task("load_cassandra", "serving_load_job.py")
        validate = PythonOperator(task_id="validate_pipeline", python_callable=_validate,
                                  op_kwargs={"run_id": "{{ run_id }}"}, retries=0)
        cache = PythonOperator(task_id="refresh_api_cache", python_callable=_refresh_cache)
        load >> validate >> cache

    record = PythonOperator(task_id="record_run", python_callable=_record_run,
                            op_kwargs={"run_id": "{{ run_id }}"},
                            trigger_rule=TriggerRule.ALL_DONE, retries=0)

    check_infra >> preparacao >> produce >> lakehouse >> serving >> record
