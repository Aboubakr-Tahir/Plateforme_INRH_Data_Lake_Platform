"""Pipeline qualité Bronze -> Silver avec persistance PostgreSQL."""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any

import psycopg2
import pandas as pd
from dotenv import load_dotenv
from generator.generate_all import main as generate_mock_data

from data_pipeline.celery_app import app
from data_pipeline.minio_client import (
    get_client,
    read_from_bronze,
    upload_to_bronze,
    write_to_gold,
    write_to_silver,
)
from quality_engine.anomaly_detector import hybrid_anomaly_scan
from quality_engine.dimensions.completeness import evaluate_dataset_completeness
from quality_engine.dimensions.consistency import evaluate_cross_source_consistency
from quality_engine.dimensions.uniqueness import evaluate_source_uniqueness
from quality_engine.dimensions.validity import evaluate_source_validity
from quality_engine.scoring import compute_global_score


SOURCE_OBJECTS = {
    "VMS": "vms/vms_batch_01.csv",
    "SALES": "sales/sales_batch_01.csv",
    "LOGBOOK": "logbook/logbook_batch_01.csv",
    "ENV": "env/env_batch_01.csv",
}
SOURCE_FILES = {
    "VMS": "vms_batch_01.csv",
    "SALES": "sales_batch_01.csv",
    "LOGBOOK": "logbook_batch_01.csv",
    "ENV": "env_batch_01.csv",
}

MANDATORY_COLUMNS = {
    "VMS": ["vms_id", "vessel_id", "timestamp", "latitude", "longitude", "speed"],
    "SALES": [
        "sale_id", "vessel_id", "trip_id", "sale_date",
        "port_id", "species_code", "quantity_kg", "total_price",
    ],
    "LOGBOOK": [
        "log_id", "vessel_id", "trip_id", "log_date", "species_code",
        "weight_kg", "gear_type", "latitude", "longitude",
    ],
    "ENV": [
        "env_id", "sensor_id", "timestamp", "latitude", "longitude",
        "sea_surface_temp",
    ],
}


def get_database_connection():
    """Ouvre une connexion PostgreSQL avec la configuration du fichier .env."""
    load_dotenv()
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "inrh_metadata"),
        user=os.getenv("DB_USER", "inrh_admin"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )


def initialize_metadata_tables(connection) -> None:
    """Crée les tables de gouvernance si elles n'existent pas encore."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_metadata (
                batch_id VARCHAR(100) PRIMARY KEY,
                started_at TIMESTAMPTZ NOT NULL,
                completed_at TIMESTAMPTZ,
                status VARCHAR(20) NOT NULL,
                source_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS quality_scores (
                id BIGSERIAL PRIMARY KEY,
                batch_id VARCHAR(100) NOT NULL REFERENCES batch_metadata(batch_id),
                source_type VARCHAR(20) NOT NULL,
                global_score NUMERIC(5, 2) NOT NULL,
                grade VARCHAR(30) NOT NULL,
                status VARCHAR(20) NOT NULL,
                completeness_score NUMERIC(5, 2) NOT NULL,
                validity_score NUMERIC(5, 2) NOT NULL,
                uniqueness_score NUMERIC(5, 2) NOT NULL,
                consistency_score NUMERIC(5, 2) NOT NULL,
                anomaly_count INTEGER NOT NULL DEFAULT 0,
                details JSONB NOT NULL
            );

            CREATE TABLE IF NOT EXISTS anomaly_logs (
                id BIGSERIAL PRIMARY KEY,
                batch_id VARCHAR(100) NOT NULL REFERENCES batch_metadata(batch_id),
                source_type VARCHAR(20) NOT NULL,
                row_index INTEGER NOT NULL,
                entity_id VARCHAR(100),
                rule VARCHAR(150) NOT NULL,
                method VARCHAR(30) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL
            );
            """
        )
    connection.commit()


def _quality_flag(dataframe, source: str, anomalies: list[dict[str, Any]], quality: dict[str, Any]) -> None:
    """Ajoute un statut lisible par ligne à un DataFrame traité."""
    flags = {index: "VALID" for index in dataframe.index}

    for index in quality["completeness"]["missing_indices"]:
        flags[index] = "WARNING"
    for index in quality["validity"]["invalid_indices"]:
        flags[index] = "CRITICAL"
    for index in quality["uniqueness"]["duplicate_indices"]:
        if flags.get(index) != "CRITICAL":
            flags[index] = "WARNING"

    for anomaly in anomalies:
        index = anomaly["row_index"]
        if anomaly["severity"] == "CRITICAL":
            flags[index] = "CRITICAL"
        elif flags.get(index) == "VALID":
            flags[index] = "WARNING"

    dataframe["quality_flag"] = [flags.get(index, "VALID") for index in dataframe.index]


def _dimension_scores(dataframe, source: str, consistency_score: float) -> dict[str, Any]:
    completeness = evaluate_dataset_completeness(
        dataframe, mandatory_columns=MANDATORY_COLUMNS[source]
    )
    validity = evaluate_source_validity(dataframe, source)
    uniqueness = evaluate_source_uniqueness(dataframe, source)
    return {
        "completeness": completeness,
        "validity": validity,
        "uniqueness": uniqueness,
        "consistency": {"score": consistency_score},
    }


def build_gold_aggregates(
    dataframes: dict[str, Any],
    batch_id: str,
    client,
    quality_sources: dict[str, Any],
) -> dict[str, str]:
    """Construit les indicateurs métier et les écrit dans Gold."""
    sales = dataframes["SALES"].copy()
    logbook = dataframes["LOGBOOK"].copy()
    env = dataframes["ENV"].copy()

    sales["sale_date"] = sales["sale_date"].astype(str)
    sales["month"] = sales["sale_date"].str[:7]
    sales_by_port_species = (
        sales.groupby(["month", "port_id", "species_code"], as_index=False)
        .agg(
            total_sold_kg=("quantity_kg", "sum"),
            total_sales_mad=("total_price", "sum"),
            average_price_mad=("total_price", "mean"),
            sales_count=("sale_id", "count"),
        )
    )

    logbook["log_date"] = logbook["log_date"].astype(str)
    logbook["month"] = logbook["log_date"].str[:7]
    catches_by_species = (
        logbook.groupby(["month", "species_code"], as_index=False)
        .agg(
            total_catch_kg=("weight_kg", "sum"),
            trips_count=("trip_id", "nunique"),
        )
    )

    env["timestamp"] = pd.to_datetime(env["timestamp"], errors="coerce")
    env["month"] = env["timestamp"].dt.strftime("%Y-%m")
    environment_by_sensor = (
        env.groupby(["month", "sensor_id"], as_index=False)
        .agg(
            average_temperature=("sea_surface_temp", "mean"),
            average_salinity=("salinity", "mean"),
            average_chlorophyll=("chlorophyll_a", "mean"),
            measurements_count=("env_id", "count"),
        )
    )
    quality_kpis = pd.DataFrame(
        [
            {
                "batch_id": batch_id,
                "source_type": source,
                "global_score": details["score"]["global_score"],
                "grade": details["score"]["grade"],
                "status": details["score"]["status"],
                "anomaly_count": details["anomaly_count"],
                "critical_anomaly_count": details["critical_anomaly_count"],
                "warning_anomaly_count": details["warning_anomaly_count"],
            }
            for source, details in quality_sources.items()
        ]
    )

    prefix = f"{batch_id}/"
    return {
        "sales_by_port_species": write_to_gold(
            sales_by_port_species,
            prefix + "sales_by_port_species.parquet",
            client,
        ),
        "catches_by_species": write_to_gold(
            catches_by_species,
            prefix + "catches_by_species.parquet",
            client,
        ),
        "environment_by_sensor": write_to_gold(
            environment_by_sensor,
            prefix + "environment_by_sensor.parquet",
            client,
        ),
        "quality_kpis": write_to_gold(
            quality_kpis,
            prefix + "quality_kpis.parquet",
            client,
        ),
    }


def run_quality_pipeline(batch_id: str) -> dict[str, Any]:
    """Traite les quatre sources d'un batch et persiste ses résultats."""
    if not batch_id or not batch_id.strip():
        raise ValueError("batch_id est obligatoire.")

    client = get_client()
    connection = get_database_connection()
    started_at = datetime.now(timezone.utc)
    results: dict[str, Any] = {"batch_id": batch_id, "sources": {}}

    try:
        initialize_metadata_tables(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO batch_metadata (batch_id, started_at, status, source_count)
                VALUES (%s, %s, 'GENERATING', 0)
                ON CONFLICT (batch_id) DO UPDATE
                SET started_at = EXCLUDED.started_at,
                    completed_at = NULL,
                    status = 'RUNNING',
                    source_count = 0
                """,
                (batch_id, started_at),
            )
        connection.commit()

        generate_mock_data()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE batch_metadata SET status = 'INGESTING' WHERE batch_id = %s",
                (batch_id,),
            )
        connection.commit()
        data_directory = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "generator", "mock_data"
        )
        batch_source_objects = {}
        for source, filename in SOURCE_FILES.items():
            object_name = f"{source.lower()}/{batch_id}/{filename}"
            upload_to_bronze(os.path.join(data_directory, filename), object_name, client)
            batch_source_objects[source] = object_name

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE batch_metadata SET status = 'PROCESSING' WHERE batch_id = %s",
                (batch_id,),
            )
        connection.commit()
        dataframes = {
            source: read_from_bronze(object_name, client)
            for source, object_name in batch_source_objects.items()
        }
        consistency = evaluate_cross_source_consistency(
            dataframes["LOGBOOK"], dataframes["SALES"]
        )

        with connection.cursor() as cursor:
            for source, dataframe in dataframes.items():
                consistency_score = (
                    consistency["score"] if source in {"LOGBOOK", "SALES"} else 100.0
                )
                dimensions = _dimension_scores(dataframe, source, consistency_score)
                anomalies = hybrid_anomaly_scan(dataframe, source)

                if source == "SALES":
                    consistency_ids = set(consistency["anomalous_sales_ids"])
                    for sale_index, sale_id in dataframe["sale_id"].items():
                        if sale_id in consistency_ids:
                            anomalies.append({
                                "row_index": sale_index,
                                "entity_id": str(sale_id),
                                "rule": "CROSS_SOURCE_LOGBOOK_SALES_INCONSISTENCY",
                                "method": "DETERMINISTIC",
                                "severity": "WARNING",
                                "message": "Incohérence détectée entre LOGBOOK et SALES.",
                            })

                _quality_flag(dataframe, source, anomalies, dimensions)
                silver_object = (
                    f"{source.lower()}/{batch_id}/{source.lower()}_{batch_id}.parquet"
                )
                write_to_silver(dataframe, silver_object, client)

                score = compute_global_score(
                    dimensions["completeness"]["score"],
                    dimensions["validity"]["score"],
                    dimensions["uniqueness"]["score"],
                    consistency_score,
                )
                cursor.execute(
                    """
                    INSERT INTO quality_scores (
                        batch_id, source_type, global_score, grade, status,
                        completeness_score, validity_score, uniqueness_score,
                        consistency_score, anomaly_count, details
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        batch_id, source, score["global_score"], score["grade"],
                        score["status"], dimensions["completeness"]["score"],
                        dimensions["validity"]["score"], dimensions["uniqueness"]["score"],
                        consistency_score, len(anomalies),
                        json.dumps(dimensions, default=str),
                    ),
                )

                for anomaly in anomalies:
                    cursor.execute(
                        """
                        INSERT INTO anomaly_logs (
                            batch_id, source_type, row_index, entity_id,
                            rule, method, severity, message
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            batch_id, source, anomaly["row_index"],
                            anomaly.get("entity_id"), anomaly["rule"],
                            anomaly["method"], anomaly["severity"],
                            anomaly["message"],
                        ),
                    )

                results["sources"][source] = {
                    "rows": len(dataframe),
                    "score": score,
                    "anomaly_count": len(anomalies),
                    "critical_anomaly_count": sum(
                        anomaly["severity"] == "CRITICAL" for anomaly in anomalies
                    ),
                    "warning_anomaly_count": sum(
                        anomaly["severity"] == "WARNING" for anomaly in anomalies
                    ),
                    "silver_object": silver_object,
                }

            results["gold_objects"] = build_gold_aggregates(
                dataframes, batch_id, client, results["sources"]
            )
            cursor.execute(
                """
                UPDATE batch_metadata
                SET completed_at = %s, status = 'COMPLETED', source_count = %s
                WHERE batch_id = %s
                """,
                (datetime.now(timezone.utc), len(dataframes), batch_id),
            )
        connection.commit()
        return results
    except Exception:
        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE batch_metadata SET status = 'FAILED' WHERE batch_id = %s",
                (batch_id,),
            )
        connection.commit()
        raise
    finally:
        connection.close()


@app.task(
    bind=True,
    name="data_pipeline.run_quality_pipeline",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=3,
)
def run_quality_pipeline_task(self, batch_id: str) -> dict[str, Any]:
    """Exécute le pipeline qualité dans un worker Celery."""
    return run_quality_pipeline(batch_id)
