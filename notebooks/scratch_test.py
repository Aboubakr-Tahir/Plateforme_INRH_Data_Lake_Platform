"""Test local du chargement des quatre sources INRH dans MinIO."""

from pathlib import Path

from data_pipeline.minio_client import (
    ensure_buckets,
    get_client,
    upload_to_bronze,
    read_from_bronze,
    write_to_silver,
)

DATASETS = {
    "vms": "vms_batch_01.csv",
    "sales": "sales_batch_01.csv",
    "logbook": "logbook_batch_01.csv",
    "env": "env_batch_01.csv",
}


def main() -> None:
    client = get_client()
    ensure_buckets(client)

    for source, filename in DATASETS.items():
        local_path = Path("generator/mock_data") / filename
        bronze_object = f"{source}/{filename}"

        try:
            upload_to_bronze(local_path, bronze_object, client)
            print(f"[BRONZE] Uploadé : {bronze_object}")
        except FileExistsError:
            print(f"[BRONZE] Déjà présent, conservation de l'original : {bronze_object}")

        dataframe = read_from_bronze(bronze_object, client)
        silver_object = f"{source}/{filename.removesuffix('.csv')}.parquet"
        write_to_silver(dataframe, silver_object, client)
        print(f"[SILVER] Écrit : {silver_object} ({len(dataframe)} lignes)")


if __name__ == "__main__":
    main()