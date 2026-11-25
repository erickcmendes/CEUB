"""Garante o bucket e o CSV de origem no MinIO (camada raw / landing).

O CSV original da UCI é publicado em s3://air-quality/raw/airquality.csv sem
nenhuma alteração; é dele que o Producer lê. Se o objeto já existir com o
mesmo conteúdo (ETag = MD5), o upload é pulado, o que deixa a tarefa idempotente.
"""
import hashlib
import os

from botocore.exceptions import ClientError

import settings


def ensure_bucket(s3, bucket):
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"Bucket '{bucket}' já existe.")
    except ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"Bucket '{bucket}' criado.")


def upload_source(local_path=None):
    local_path = local_path or settings.LOCAL_SOURCE_CSV
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"CSV de origem não encontrado: {local_path}")

    s3 = settings.s3_client()
    ensure_bucket(s3, settings.BUCKET)

    with open(local_path, "rb") as fh:
        body = fh.read()
    md5 = hashlib.md5(body).hexdigest()  # noqa: S324 - comparação com ETag, não segurança

    try:
        head = s3.head_object(Bucket=settings.BUCKET, Key=settings.SOURCE_KEY)
        if head["ETag"].strip('"') == md5:
            print(f"s3://{settings.BUCKET}/{settings.SOURCE_KEY} já está atualizado (md5={md5}).")
            return {"key": settings.SOURCE_KEY, "bytes": len(body), "md5": md5, "uploaded": False}
    except ClientError:
        pass

    s3.put_object(Bucket=settings.BUCKET, Key=settings.SOURCE_KEY, Body=body, ContentType="text/csv")
    print(f"Enviado {local_path} -> s3://{settings.BUCKET}/{settings.SOURCE_KEY} ({len(body)} bytes, md5={md5}).")
    return {"key": settings.SOURCE_KEY, "bytes": len(body), "md5": md5, "uploaded": True}


if __name__ == "__main__":
    upload_source()
