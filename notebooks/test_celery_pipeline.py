"""Test d'exécution asynchrone du pipeline qualité avec Celery et Redis."""

from data_pipeline.tasks import run_quality_pipeline_task


def main() -> None:
    result = run_quality_pipeline_task.delay("batch_01")
    print(f"Tâche envoyée à Redis : {result.id}")
    output = result.get(timeout=180, propagate=True)

    assert output["batch_id"] == "batch_01"
    assert set(output["sources"]) == {"VMS", "SALES", "LOGBOOK", "ENV"}
    print("Tâche Celery terminée avec succès.")
    for source, details in output["sources"].items():
        print(
            f"{source}: score={details['score']['global_score']}%, "
            f"anomalies={details['anomaly_count']}"
        )


if __name__ == "__main__":
    main()
