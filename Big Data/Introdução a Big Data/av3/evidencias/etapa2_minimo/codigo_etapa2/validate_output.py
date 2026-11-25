"""Validação da saída: relê o Parquet no MinIO com um leitor independente
(PyArrow, sem Spark) e confere contagens, schema e integridade.

Falha (exceção) se qualquer verificação não passar, e a DAG fica vermelha.
"""
import json
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from pyarrow import fs

import settings

EXPECTED_DOUBLE = [
    "co_mg_m3", "nmhc_ug_m3", "benzene_ug_m3", "nox_ppb", "no2_ug_m3", "temperature_c",
    "relative_humidity_pct", "absolute_humidity",
]


def s3fs():
    u = urlparse(settings.MINIO_ENDPOINT)
    return fs.S3FileSystem(endpoint_override=u.netloc, scheme=u.scheme,
                           access_key=settings.MINIO_ACCESS_KEY, secret_key=settings.MINIO_SECRET_KEY,
                           region="us-east-1")


def load_spark_report(run_id):
    key = f"{settings.REPORTS_PREFIX}/run_id={run_id}/spark_report.json"
    body = settings.s3_client().get_object(Bucket=settings.BUCKET, Key=key)["Body"].read()
    return json.loads(body)


def validate(run_id, produced=None):
    report = load_spark_report(run_id)
    path = f"{settings.BUCKET}/{settings.PROCESSED_PREFIX}"
    dataset = ds.dataset(path, filesystem=s3fs(), format="parquet", partitioning="hive")
    table = dataset.to_table()
    n_files = len(dataset.files)

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"[{'OK ' if ok else 'ERRO'}] {name}: {detail}")

    check("dataset não vazio", table.num_rows > 0, f"{table.num_rows} linhas em {n_files} arquivos Parquet")
    check("linhas = relatório do Spark", table.num_rows == report["rows_written"],
          f"pyarrow={table.num_rows} spark={report['rows_written']}")
    if produced is not None:
        check("mensagens produzidas = consumidas pelo Spark", produced == report["input_messages"],
              f"producer={produced} spark={report['input_messages']}")
    balance = (report["rows_written"] + report["malformed_messages"]
               + report["invalid_timestamp"] + report["duplicates_removed"])
    check("balanço entrada = saída + descartes", balance == report["input_messages"],
          f"{report['rows_written']} + {report['malformed_messages']} + {report['invalid_timestamp']} "
          f"+ {report['duplicates_removed']} = {balance} (entrada {report['input_messages']})")

    schema = table.schema
    check("event_ts é timestamp", pa.types.is_timestamp(schema.field("event_ts").type),
          str(schema.field("event_ts").type))
    wrong = [c for c in EXPECTED_DOUBLE if not pa.types.is_float64(schema.field(c).type)]
    check("medidas são double", not wrong, f"fora do tipo: {wrong}" if wrong else f"{len(EXPECTED_DOUBLE)} colunas float64")
    check("event_ts sem nulos", table["event_ts"].null_count == 0, f"nulos={table['event_ts'].null_count}")
    n_unique = len(pc.unique(table["event_ts"]))
    check("event_ts único", n_unique == table.num_rows, f"únicos={n_unique}")
    sentinels = sum(pc.sum(pc.equal(table[c], -200.0)).as_py() or 0 for c in EXPECTED_DOUBLE)
    check("sem sentinela -200 na saída", sentinels == 0, f"ocorrências={sentinels}")
    mn, mx = pc.min_max(table["event_ts"]).values()
    check("intervalo temporal coerente", mn.as_py().year == 2004 and mx.as_py().year == 2005,
          f"{mn.as_py()} -> {mx.as_py()}")
    partitions = sorted({f.split(settings.PROCESSED_PREFIX + "/")[1].rsplit("/", 1)[0] for f in dataset.files})
    check("particionado por ano/mês", len(partitions) >= 12, f"{len(partitions)} partições: {partitions[0]} ... {partitions[-1]}")

    # Consulta de exemplo sobre os dados recuperados: CO médio por hora do dia
    df = table.select(["hour", "co_mg_m3", "no2_ug_m3", "temperature_c"]).to_pandas()
    by_hour = df.groupby("hour")[["co_mg_m3", "no2_ug_m3"]].mean().round(2)
    print("\nConsulta: média de CO (mg/m³) e NO2 (µg/m³) por hora do dia")
    print(by_hour.to_string())
    print(f"\nTemperatura média geral: {df['temperature_c'].mean():.1f} °C | CO médio: {df['co_mg_m3'].mean():.2f} mg/m³")

    failed = [c for c in checks if not c["ok"]]
    result = {
        "run_id": run_id,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "rows": table.num_rows,
        "files": n_files,
        "partitions": len(partitions),
        "checks": checks,
        "status": "FAILED" if failed else "PASSED",
    }
    key = f"{settings.REPORTS_PREFIX}/run_id={run_id}/validation_report.json"
    settings.s3_client().put_object(Bucket=settings.BUCKET, Key=key,
                                    Body=json.dumps(result, indent=2, ensure_ascii=False).encode(),
                                    ContentType="application/json")
    print(f"\nRelatório de validação salvo em s3://{settings.BUCKET}/{key}")
    if failed:
        raise ValueError(f"{len(failed)} verificação(ões) falharam: {[c['check'] for c in failed]}")
    print(f"VALIDAÇÃO OK: {len(checks)} verificações aprovadas.")
    return result


if __name__ == "__main__":
    validate(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
