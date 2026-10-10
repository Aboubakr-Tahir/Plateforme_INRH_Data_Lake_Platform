"""Test des agrégations métier écrites dans la couche Gold."""

from data_pipeline.minio_client import get_client, read_from_gold
from data_pipeline.tasks import run_quality_pipeline


def main() -> None:
    result = run_quality_pipeline("batch_01")
    client = get_client()

    expected_objects = {
        "sales_by_port_species": "batch_01/sales_by_port_species.parquet",
        "catches_by_species": "batch_01/catches_by_species.parquet",
        "environment_by_sensor": "batch_01/environment_by_sensor.parquet",
        "quality_kpis": "batch_01/quality_kpis.parquet",
    }
    assert result["gold_objects"] == expected_objects

    checks = {
        "sales_by_port_species": {"month", "port_id", "species_code", "total_sold_kg"},
        "catches_by_species": {"month", "species_code", "total_catch_kg"},
        "environment_by_sensor": {"month", "sensor_id", "average_temperature"},
        "quality_kpis": {"batch_id", "source_type", "global_score", "anomaly_count"},
    }
    for name, object_name in expected_objects.items():
        dataframe = read_from_gold(object_name, client)
        assert checks[name].issubset(dataframe.columns)
        assert not dataframe.empty
        print(f"{name}: {len(dataframe)} lignes")

    print("Couche Gold validée avec succès.")


if __name__ == "__main__":
    main()
