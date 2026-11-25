# Prints das interfaces

Capturas de tela das interfaces web com o ambiente no ar (2026-11-25), complementando
os logs em `evidencias/etapa3/` e o notebook executado.

| Arquivo | Conteúdo |
|---|---|
| `01_airflow_DAG_details.png` | Airflow: detalhes da DAG `pipeline_airquality` |
| `01_airflow_grafo.png` | Airflow: grafo da DAG, com os task groups `preparacao`, `lakehouse` e `serving` |
| `02_airflow_execucoes.png` | Airflow: grade de execuções e tentativas |
| `03_spark_master.png` | Spark Master: worker e aplicações executadas no cluster |
| `04_minio_lakehouse.png` | Console do MinIO: bucket `air-quality` com as camadas do Lakehouse |
| `05_api_swagger.png` | API FastAPI: documentação Swagger (`/docs`) |
| `06_dashboard_visao_geral.png` | Dashboard Streamlit: KPIs, perfil horário, CO diário e alertas por dia |
| `07_dashboard_alertas.png` | Dashboard: alertas por regra e por mês |
| `08_dashboard_tempo_real.png` | Dashboard: leituras do Spark Structured Streaming |
| `09_dashboard_pipeline.png` | Dashboard: saúde da API, cache e histórico de execuções da DAG |
