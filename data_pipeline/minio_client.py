"""
Client MinIO simplifié pour le Data Lake INRH :
Gère automatiquement les 3 buckets du Medallion Architecture :
- inrh-bronze : fichiers bruts horodatés (CSV / JSON)
- inrh-silver : données nettoyées, validées et enrichies (Parquet)
- inrh-gold   : indicateurs agrégés et KPIs scientifiques (Parquet)
"""

import os
import io
from typing import Optional
import pandas as pd
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "inrh_minio_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "inrh_minio_password")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1")

BUCKETS = {
    "bronze": "inrh-bronze",
    "silver": "inrh-silver",
    "gold": "inrh-gold"
}


def get_minio_client() -> Optional[Minio]:
    """Retourne une instance du client MinIO."""
    try:
        client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except Exception as e:
        print(f"⚠️ Erreur de connexion à MinIO : {e}")
        return None


def init_lake_buckets() -> bool:
    """Crée les 3 buckets Medallion (Bronze, Silver, Gold) s'ils n'existent pas encore."""
    client = get_minio_client()
    if not client:
        return False

    for layer, bucket_name in BUCKETS.items():
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"🪣 Bucket '{bucket_name}' ({layer}) créé avec succès.")
        except S3Error as err:
            print(f"❌ Erreur lors de la création du bucket {bucket_name}: {err}")
            return False
    return True


def upload_df_to_lake(df: pd.DataFrame, layer: str, object_name: str, file_format: str = "parquet") -> bool:
    """
    Téléverse un DataFrame Pandas vers une couche du Data Lake (bronze, silver ou gold).
    Exemple d'object_name : 'vms/2026-10-01/batch_01.parquet'
    """
    client = get_minio_client()
    if not client:
        print("❌ Impossible de téléverser : Client MinIO indisponible.")
        return False

    bucket = BUCKETS.get(layer.lower())
    if not bucket:
        raise ValueError(f"Couche inconnue '{layer}'. Choisir parmi: bronze, silver, gold.")

    buffer = io.BytesIO()
    if file_format == "parquet":
        df.to_parquet(buffer, index=False)
    elif file_format == "csv":
        df.to_csv(buffer, index=False)
    else:
        raise ValueError("Format non supporté. Utiliser 'parquet' ou 'csv'.")

    buffer.seek(0)
    data_length = buffer.getbuffer().nbytes

    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=buffer,
        length=data_length,
        content_type="application/octet-stream"
    )
    print(f"✅ Téléversé avec succès dans [{bucket}] -> {object_name}")
    return True


def read_df_from_lake(layer: str, object_name: str, file_format: str = "parquet") -> Optional[pd.DataFrame]:
    """Lit un fichier du Data Lake directement dans un DataFrame Pandas."""
    client = get_minio_client()
    if not client:
        return None

    bucket = BUCKETS.get(layer.lower())
    try:
        response = client.get_object(bucket, object_name)
        data = io.BytesIO(response.read())
        response.close()
        response.release_conn()

        if file_format == "parquet":
            return pd.read_parquet(data)
        elif file_format == "csv":
            return pd.read_csv(data)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de [{bucket}/{object_name}]: {e}")
        return None
