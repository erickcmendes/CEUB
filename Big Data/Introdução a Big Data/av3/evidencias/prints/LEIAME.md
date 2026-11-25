# Prints das interfaces

Os logs e as saídas de texto em `evidencias/etapa3/` e o notebook executado já comprovam cada etapa.
Este diretório recebe as capturas de tela das interfaces web (com o ambiente no ar: `./scripts/setup.sh`):

| Arquivo sugerido | Onde capturar |
|---|---|
| `01_airflow_grafo.png` | Airflow http://localhost:8080 → DAG `pipeline_airquality` → Graph (execução `manual__av3_rerun_20261125T135717`) |
| `02_airflow_execucoes.png` | Airflow → Grid, mostrando as execuções e as tentativas (retries) |
| `03_spark_master.png` | Spark Master http://localhost:8081 (aplicações concluídas e, com o streaming ligado, a ativa) |
| `04_minio_lakehouse.png` | Console do MinIO http://localhost:9001 → bucket `air-quality/lakehouse` |
| `05_api_swagger.png` | http://localhost:8000/docs |
| `06_dashboard_visao_geral.png` | Dashboard http://localhost:8501 → aba Visão geral |
| `07_dashboard_alertas.png` | Dashboard → aba Alertas |
| `08_dashboard_tempo_real.png` | Dashboard → aba Tempo real (com `./scripts/streaming_demo.sh` rodando) |
| `09_dashboard_pipeline.png` | Dashboard → aba Pipeline (histórico de execuções e cache) |
