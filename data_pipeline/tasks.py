"""
Tâches Celery pour le traitement Bronze -> Silver -> Gold.
Peut également être exécuté directement en ligne de commande :
python data_pipeline/tasks.py
"""

import os
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Assurer l'accès aux modules parents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_engine.dimensions.completeness import evaluate_dataset_completeness
from quality_engine.dimensions.validity import check_maritime_coordinates, check_range_validity
from quality_engine.dimensions.uniqueness import check_uniqueness
from quality_engine.dimensions.consistency import check_date_chronology
from quality_engine.anomaly_detector import hybrid_anomaly_scan
from quality_engine.scoring import compute_global_score
from data_pipeline.minio_client import upload_df_to_lake, read_df_from_lake, init_lake_buckets

try:
    from data_pipeline.celery_app import app
except Exception:
    app = None


def process_dataset_quality(df: pd.DataFrame, source_type: str, batch_id: str) -> dict:
    """
    Exécute le pipeline de qualité complet sur un DataFrame :
    1. Calcule les 4 dimensions
    2. Détecte les anomalies hybrides
    3. Calcule le score global
    4. Retourne les données nettoyées et le rapport de métadonnées
    """
    source = source_type.upper()
    print(f"\n🔍 Analyse qualité en cours pour le lot [{batch_id}] ({source})...")

    # 1. Complétude
    comp_res = evaluate_dataset_completeness(df)
    comp_score = comp_res["score"]

    # 2. Validité
    if source == "VMS":
        geo_res = check_maritime_coordinates(df)
        speed_res = check_range_validity(df, "speed_knots", 0.0, 35.0)
        validity_score = round((geo_res["score"] + speed_res["score"]) / 2, 2)
    elif source == "ENV":
        temp_res = check_range_validity(df, "water_temp_celsius", 10.0, 30.0)
        validity_score = temp_res["score"]
    elif source == "SALES":
        price_res = check_range_validity(df, "price_mad_per_kg", 0.01, 1000.0)
        validity_score = price_res["score"]
    elif source == "LOGBOOK":
        weight_res = check_range_validity(df, "catch_weight_kg", 0.1, 50000.0)
        validity_score = weight_res["score"]
    else:
        validity_score = 100.0

    # 3. Unicité
    uniq_res = check_uniqueness(df)
    uniq_score = uniq_res["score"]

    # 4. Cohérence
    if source == "LOGBOOK":
        chrono_res = check_date_chronology(df, "departure_date", "return_date")
        consist_score = chrono_res["score"]
    else:
        consist_score = 100.0

    # 5. Détection d'anomalies hybride
    anomalies = hybrid_anomaly_scan(df, source)

    # 6. Score Global
    scoring_result = compute_global_score(
        completeness_score=comp_score,
        validity_score=validity_score,
        uniqueness_score=uniq_score,
        consistency_score=consist_score
    )

    # 7. Préparation de la donnée Silver (ajout d'une colonne de validation)
    silver_df = df.copy()
    anomalous_indices = set([a["row_index"] for a in anomalies])
    silver_df["is_quality_valid"] = ~silver_df.index.isin(anomalous_indices)
    silver_df["processed_at"] = datetime.utcnow().isoformat()
    silver_df["batch_id"] = batch_id

    report = {
        "batch_id": batch_id,
        "source": source,
        "total_rows": len(df),
        "valid_rows": int(silver_df["is_quality_valid"].sum()),
        "anomalies_detected": len(anomalies),
        "global_score": scoring_result["global_score"],
        "grade": scoring_result["grade"],
        "status": scoring_result["status"],
        "sub_scores": scoring_result["sub_scores"],
        "anomalies": anomalies
    }

    print(f"📊 Résultats Qualité : Score={report['global_score']}% | Grade={report['grade']} | Anomalies={len(anomalies)}")
    return {"silver_df": silver_df, "report": report}


def run_pipeline_for_source(source_type: str, local_csv_path: str):
    """Exécute le pipeline complet depuis un fichier CSV local vers MinIO."""
    batch_date = datetime.now().strftime("%Y-%m-%d")
    batch_id = f"{source_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    df = pd.read_csv(local_csv_path)

    # Tente d'envoyer dans Bronze (MinIO)
    try:
        bronze_path = f"{source_type.lower()}/{batch_date}/{batch_id}.csv"
        upload_df_to_lake(df, "bronze", bronze_path, file_format="csv")
    except Exception as e:
        print(f"ℹ️ MinIO non accessible pour Bronze : {e}")

    # Exécution du moteur qualité
    res = process_dataset_quality(df, source_type, batch_id)
    silver_df = res["silver_df"]
    report = res["report"]

    # Tente d'envoyer dans Silver (MinIO en Parquet)
    try:
        silver_path = f"{source_type.lower()}/{batch_date}/{batch_id}.parquet"
        upload_df_to_lake(silver_df, "silver", silver_path, file_format="parquet")
    except Exception as e:
        print(f"ℹ️ MinIO non accessible pour Silver : {e}")

    return report


if __name__ == "__main__":
    print("🚀 Test direct du Pipeline de Qualité INRH...")
    mock_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generator", "mock_data")
    vms_file = os.path.join(mock_dir, "vms_batch_01.csv")

    if not os.path.exists(vms_file):
        print("⚠️ Données non trouvées. Génération des données de test...")
        from generator.generate_all import main as gen_main
        gen_main()

    # Initialisation optionnelle des buckets MinIO
    init_lake_buckets()

    # Lancement du test
    report = run_pipeline_for_source("VMS", vms_file)
    print("\n✅ Fin du traitement. Rapport résumé :")
    print(f"Lot : {report['batch_id']}")
    print(f"Score Global : {report['global_score']}% ({report['grade']})")
    print(f"Anomalies : {report['anomalies_detected']} détectées.")
