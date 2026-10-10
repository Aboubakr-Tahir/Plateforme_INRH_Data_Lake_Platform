"""Test d'intégration du pipeline qualité avec MinIO et PostgreSQL."""

from data_pipeline.tasks import run_quality_pipeline


def main() -> None:
    result = run_quality_pipeline("batch_01")

    assert set(result["sources"]) == {"VMS", "SALES", "LOGBOOK", "ENV"}
    for source, details in result["sources"].items():
        assert details["rows"] > 0
        assert 0 <= details["score"]["global_score"] <= 100
        assert details["anomaly_count"] >= 0
        print(
            f"{source}: {details['rows']} lignes, "
            f"score={details['score']['global_score']}%, "
            f"anomalies={details['anomaly_count']}"
        )

    print("Pipeline qualité validé : Silver et PostgreSQL ont été alimentés.")


if __name__ == "__main__":
    main()
