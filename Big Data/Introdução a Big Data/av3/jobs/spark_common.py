"""SparkSession com Delta Lake, Cassandra Connector e S3A (MinIO) configurados."""
from pyspark.sql import SparkSession

import settings


def build_spark(app_name):
    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        # Delta Lake + Cassandra
        .config("spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension,com.datastax.spark.connector.CassandraSparkExtensions")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.cassandra.connection.host", settings.CASSANDRA_HOST)
        .config("spark.cassandra.output.consistency.level", "LOCAL_ONE")
        # MinIO via S3A
        .config("spark.hadoop.fs.s3a.endpoint", settings.MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", settings.MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", settings.MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        # Tabelas pequenas: o padrão (50 partições para o estado do snapshot Delta)
        # gera dezenas de tarefas minúsculas e gasta memória à toa.
        .config("spark.databricks.delta.snapshotPartitions", "4")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    sc = spark.sparkContext
    print(f"Spark {spark.version} | master={sc.master} | app={sc.applicationId} | {app_name}")
    return spark


def is_delta(spark, path):
    from delta.tables import DeltaTable

    return DeltaTable.isDeltaTable(spark, path)


def last_operation(spark, path):
    """Versão e métricas da última operação registrada no log Delta."""
    from delta.tables import DeltaTable

    row = DeltaTable.forPath(spark, path).history(1).collect()[0]
    return {"version": row["version"], "operation": row["operation"],
            "metrics": dict(row["operationMetrics"] or {})}
