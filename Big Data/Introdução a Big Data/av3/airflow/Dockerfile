# Imagem do Airflow estendida para:
#  - rodar o driver PySpark (Java 17 + pyspark com a mesma versao do cluster)
#  - Delta Lake (delta-spark) e Spark Cassandra Connector
#  - falar com Kafka (confluent-kafka), MinIO (boto3 / pyarrow / deltalake), Cassandra e Redis
FROM apache/airflow:2.10.3-python3.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps netcat-openbsd \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# JARs do Spark baixados no build (nao dependemos de --packages em tempo de execucao).
# Sao enviados aos executores via --jars pelo SparkSubmitOperator.
ARG SPARK_VERSION=3.5.3
ARG MAVEN=https://repo1.maven.org/maven2
RUN mkdir -p /opt/spark-jars && cd /opt/spark-jars \
 && curl -fsSLO ${MAVEN}/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_VERSION}.jar \
 && curl -fsSLO ${MAVEN}/org/apache/spark/spark-token-provider-kafka-0-10_2.12/${SPARK_VERSION}/spark-token-provider-kafka-0-10_2.12-${SPARK_VERSION}.jar \
 && curl -fsSLO ${MAVEN}/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar \
 && curl -fsSLO ${MAVEN}/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar \
 && curl -fsSLO ${MAVEN}/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
 && curl -fsSLO ${MAVEN}/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar \
 && curl -fsSLO ${MAVEN}/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar \
 && curl -fsSLO ${MAVEN}/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar \
 && curl -fsSLO ${MAVEN}/com/datastax/spark/spark-cassandra-connector-assembly_2.12/3.5.1/spark-cassandra-connector-assembly_2.12-3.5.1.jar \
 && chmod 644 /opt/spark-jars/*.jar

USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/requirements.txt \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.10.txt" \
 && pip install --no-cache-dir pyspark==3.5.3 delta-spark==3.2.1 "deltalake==0.22.3"
