-- Camada de serviço (serving layer) do pipeline Air Quality.
-- Modelagem orientada a consultas: cada tabela atende um acesso da API/dashboard
-- com uma única leitura de partição (ou poucas), sem ALLOW FILTERING.

CREATE KEYSPACE IF NOT EXISTS airquality
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Q1: leituras horárias de um dia  ->  WHERE day = ?
CREATE TABLE IF NOT EXISTS airquality.readings_by_day (
  day                   date,
  event_ts              timestamp,
  hour                  int,
  co_mg_m3              double,
  nmhc_ug_m3            double,
  benzene_ug_m3         double,
  nox_ppb               double,
  no2_ug_m3             double,
  temperature_c         double,
  relative_humidity_pct double,
  absolute_humidity     double,
  missing_measures      int,
  source                text,     -- batch | stream
  run_id                text,
  PRIMARY KEY ((day), event_ts)
) WITH CLUSTERING ORDER BY (event_ts ASC);

-- Q2: série diária / KPIs de um período  ->  WHERE year = ? AND day >= ? AND day <= ?
CREATE TABLE IF NOT EXISTS airquality.daily_summary (
  year             int,
  day              date,
  readings         int,
  co_avg           double,
  co_max           double,
  no2_avg          double,
  no2_max          double,
  nox_avg          double,
  benzene_avg      double,
  temp_avg         double,
  temp_min         double,
  temp_max         double,
  rh_avg           double,
  completeness_pct double,
  alerts           int,
  PRIMARY KEY ((year), day)
) WITH CLUSTERING ORDER BY (day ASC);

-- Q3: perfil médio por hora do dia  ->  WHERE profile = 'all' | 'weekday' | 'weekend'
CREATE TABLE IF NOT EXISTS airquality.hourly_profile (
  profile     text,
  hour        int,
  co_avg      double,
  no2_avg     double,
  nox_avg     double,
  benzene_avg double,
  temp_avg    double,
  readings    int,
  PRIMARY KEY ((profile), hour)
);

-- Q4: alertas de um mês, mais recentes primeiro  ->  WHERE month = 'yyyy-MM'
CREATE TABLE IF NOT EXISTS airquality.alerts_by_month (
  month     text,
  event_ts  timestamp,
  rule      text,
  severity  text,
  value     double,
  threshold double,
  source    text,
  PRIMARY KEY ((month), event_ts, rule)
) WITH CLUSTERING ORDER BY (event_ts DESC, rule ASC);

-- Q5: últimas leituras recebidas pelo streaming  ->  WHERE sensor_id = ? LIMIT n
-- TTL de 1 dia: é uma visão "ao vivo", não histórico.
CREATE TABLE IF NOT EXISTS airquality.latest_readings (
  sensor_id             text,
  received_at           timestamp,
  event_ts              timestamp,
  co_mg_m3              double,
  no2_ug_m3             double,
  nox_ppb               double,
  benzene_ug_m3         double,
  temperature_c         double,
  relative_humidity_pct double,
  alert_rules           text,
  PRIMARY KEY ((sensor_id), received_at, event_ts)
) WITH CLUSTERING ORDER BY (received_at DESC, event_ts DESC)
  AND default_time_to_live = 86400;

-- Q6: histórico de execuções da DAG  ->  WHERE pipeline = ? LIMIT n
CREATE TABLE IF NOT EXISTS airquality.pipeline_runs (
  pipeline       text,
  started_at     timestamp,
  run_id         text,
  status         text,
  duration_s     double,
  rows_bronze    int,
  rows_silver    int,
  rows_inserted  int,
  rows_updated   int,
  alerts         int,
  alerts_published int,
  checks_passed  int,
  checks_total   int,
  details        text,
  PRIMARY KEY ((pipeline), started_at)
) WITH CLUSTERING ORDER BY (started_at DESC);
