"""Relatórios de execução: cada etapa grava um JSON em s3://air-quality/reports/run_id=<run>/<etapa>.json."""
import json

import settings


def report_key(run_id, stage):
    return f"{settings.REPORTS_PREFIX}/run_id={run_id}/{stage}.json"


def put_report(run_id, stage, data):
    key = report_key(run_id, stage)
    settings.s3_client().put_object(
        Bucket=settings.BUCKET, Key=key, ContentType="application/json",
        Body=json.dumps(data, indent=2, ensure_ascii=False, default=str).encode(),
    )
    print(f"Relatório '{stage}' salvo em s3://{settings.BUCKET}/{key}")
    print(f"{stage.upper()}_REPORT=" + json.dumps(data, ensure_ascii=False, default=str))
    return key


def get_report(run_id, stage):
    body = settings.s3_client().get_object(Bucket=settings.BUCKET, Key=report_key(run_id, stage))["Body"].read()
    return json.loads(body)
