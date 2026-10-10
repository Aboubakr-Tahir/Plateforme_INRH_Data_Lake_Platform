"""Accès MinIO pour les couches Bronze, Silver et Gold du Data Lake INRH."""

from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error


BRONZE_BUCKET = "bronze"
SILVER_BUCKET = "silver"
GOLD_BUCKET = "gold"
MEDALLION_BUCKETS = (BRONZE_BUCKET, SILVER_BUCKET, GOLD_BUCKET)


def get_client() -> Minio:
    """Construit un client MinIO à partir des variables du fichier ``.env``."""
    load_dotenv()

    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9010").strip()
    access_key = os.getenv("MINIO_ACCESS_KEY", "").strip()
    secret_key = os.getenv("MINIO_SECRET_KEY", "").strip()
    secure = os.getenv("MINIO_SECURE", "False").lower() in {"1", "true", "yes"}

    if not endpoint or not access_key or not secret_key:
        raise RuntimeError(
            "Configuration MinIO incomplète : MINIO_ENDPOINT, "
            "MINIO_ACCESS_KEY et MINIO_SECRET_KEY sont requis."
        )

    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def ensure_buckets(client: Optional[Minio] = None) -> list[str]:
    """Vérifie les trois buckets Medallion et crée ceux qui sont absents."""
    minio_client = client or get_client()
    existing_buckets = {bucket.name for bucket in minio_client.list_buckets()}
    created_buckets: list[str] = []

    for bucket_name in MEDALLION_BUCKETS:
        if bucket_name not in existing_buckets:
            minio_client.make_bucket(bucket_name)
            created_buckets.append(bucket_name)

    return created_buckets


def upload_to_bronze(
    file_path: str | Path,
    object_name: Optional[str] = None,
    client: Optional[Minio] = None,
) -> str:
    """Dépose un fichier brut dans Bronze sans écraser un objet existant.

    Si aucun nom d'objet n'est fourni, le fichier est rangé sous
    ``YYYY/MM/DD/<nom_du_fichier>`` afin de conserver la date d'ingestion.
    """
    source_path = Path(file_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Fichier Bronze introuvable : {source_path}")

    minio_client = client or get_client()
    ensure_buckets(minio_client)

    if object_name is None:
        ingestion_date = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        object_name = f"{ingestion_date}/{source_path.name}"
    object_name = object_name.lstrip("/")

    try:
        minio_client.stat_object(BRONZE_BUCKET, object_name)
    except S3Error as error:
        if error.code not in {"NoSuchKey", "NoSuchObject", "NotFound"}:
            raise
    else:
        raise FileExistsError(
            f"Objet Bronze déjà présent, upload refusé : "
            f"{BRONZE_BUCKET}/{object_name}"
        )

    minio_client.fput_object(BRONZE_BUCKET, object_name, str(source_path))
    return object_name


def read_from_bronze(
    object_name: str,
    client: Optional[Minio] = None,
) -> pd.DataFrame:
    """Lit un CSV depuis Bronze et le retourne sous forme de DataFrame."""
    if not object_name or object_name.endswith("/"):
        raise ValueError("object_name doit désigner un fichier CSV dans Bronze.")

    minio_client = client or get_client()
    response = minio_client.get_object(BRONZE_BUCKET, object_name.lstrip("/"))
    try:
        return pd.read_csv(response)
    finally:
        response.close()
        response.release_conn()


def write_to_silver(
    dataframe: pd.DataFrame,
    object_name: str,
    client: Optional[Minio] = None,
) -> str:
    """Écrit un DataFrame au format Parquet dans Silver."""
    if dataframe is None:
        raise ValueError("dataframe ne peut pas être None.")
    if not object_name or not object_name.lower().endswith(".parquet"):
        raise ValueError("object_name doit se terminer par '.parquet'.")

    minio_client = client or get_client()
    ensure_buckets(minio_client)
    normalized_name = object_name.lstrip("/")

    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, index=False)
    buffer.seek(0)

    minio_client.put_object(
        SILVER_BUCKET,
        normalized_name,
        buffer,
        length=buffer.getbuffer().nbytes,
        content_type="application/vnd.apache.parquet",
    )
    return normalized_name


def read_from_silver(
    object_name: str,
    client: Optional[Minio] = None,
) -> pd.DataFrame:
    """Lit un fichier Parquet depuis Silver."""
    if not object_name or not object_name.lower().endswith(".parquet"):
        raise ValueError("object_name doit désigner un fichier Parquet dans Silver.")

    minio_client = client or get_client()
    response = minio_client.get_object(SILVER_BUCKET, object_name.lstrip("/"))
    try:
        return pd.read_parquet(io.BytesIO(response.read()))
    finally:
        response.close()
        response.release_conn()


def write_to_gold(
    dataframe: pd.DataFrame,
    object_name: str,
    client: Optional[Minio] = None,
) -> str:
    """Écrit un DataFrame d'indicateurs au format Parquet dans Gold."""
    if dataframe is None:
        raise ValueError("dataframe ne peut pas être None.")
    if not object_name or not object_name.lower().endswith(".parquet"):
        raise ValueError("object_name doit se terminer par '.parquet'.")

    minio_client = client or get_client()
    ensure_buckets(minio_client)
    normalized_name = object_name.lstrip("/")

    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, index=False)
    buffer.seek(0)
    minio_client.put_object(
        GOLD_BUCKET,
        normalized_name,
        buffer,
        length=buffer.getbuffer().nbytes,
        content_type="application/vnd.apache.parquet",
    )
    return normalized_name


def read_from_gold(
    object_name: str,
    client: Optional[Minio] = None,
) -> pd.DataFrame:
    """Lit un fichier Parquet depuis Gold."""
    if not object_name or not object_name.lower().endswith(".parquet"):
        raise ValueError("object_name doit désigner un fichier Parquet dans Gold.")

    minio_client = client or get_client()
    response = minio_client.get_object(GOLD_BUCKET, object_name.lstrip("/"))
    try:
        return pd.read_parquet(io.BytesIO(response.read()))
    finally:
        response.close()
        response.release_conn()
