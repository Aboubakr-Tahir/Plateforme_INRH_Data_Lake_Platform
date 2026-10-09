"""
Module de Détection d'Anomalies Hybride :
Combine deux approches complémentaires :
1. Méthodes Déterministes : Règles métier strictes et seuils physiques
   (ex: vitesse > 35 nœuds, prix <= 0).
2. Méthodes Statistiques :
   - Z-Score : Pour les distributions gaussiennes (température ENV).
   - IQR (Boîte à moustaches) : Pour les distributions asymétriques (vitesses VMS, captures LOGBOOK).

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/anomaly_detector.py
"""

import os
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def detect_outliers_zscore(
    df: pd.DataFrame,
    column: str,
    threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Détecte les anomalies via la méthode statistique du Z-Score :
        Z = |x - moyenne| / ecart_type
    Une valeur est anormale si Z > threshold (règle des 3-sigmas).
    """
    if column not in df.columns or df.empty:
        return {
            "method": "Z_SCORE",
            "column": column,
            "threshold": threshold,
            "outlier_count": 0,
            "outlier_indices": []
        }

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 3:
        return {
            "method": "Z_SCORE",
            "column": column,
            "threshold": threshold,
            "outlier_count": 0,
            "outlier_indices": []
        }

    mean = float(series.mean())
    std = float(series.std())

    if std == 0 or np.isnan(std):
        return {
            "method": "Z_SCORE",
            "column": column,
            "threshold": threshold,
            "outlier_count": 0,
            "outlier_indices": []
        }

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # 1. Calcule le z-score pour chaque élément : z_scores = (series - mean).abs() / std
    # 2. Définis le masque 'outlier_mask' : True là où z_scores > threshold
    # -------------------------------------------------------------------------
    z_scores = None      # Remplace par (series - mean).abs() / std
    outlier_mask = None  # Remplace par z_scores > threshold

    if outlier_mask is None:
        return {
            "method": "Z_SCORE",
            "column": column,
            "threshold": threshold,
            "outlier_count": 0,
            "outlier_indices": []
        }

    outlier_indices = series[outlier_mask].index.tolist()

    return {
        "method": "Z_SCORE",
        "column": column,
        "mean": round(mean, 2),
        "std": round(std, 2),
        "threshold": threshold,
        "outlier_count": len(outlier_indices),
        "outlier_indices": outlier_indices
    }


def detect_outliers_iqr(
    df: pd.DataFrame,
    column: str,
    factor: float = 1.5
) -> Dict[str, Any]:
    """
    Détecte les anomalies via la boîte à moustaches (IQR) :
        IQR = Q3 - Q1
        Borne inférieure = Q1 - factor * IQR
        Borne supérieure = Q3 + factor * IQR
    """
    if column not in df.columns or df.empty:
        return {
            "method": "IQR",
            "column": column,
            "factor": factor,
            "outlier_count": 0,
            "outlier_indices": []
        }

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 4:
        return {
            "method": "IQR",
            "column": column,
            "factor": factor,
            "outlier_count": 0,
            "outlier_indices": []
        }

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 2/2 :
    # 1. Calcule q1 (percentile 0.25) et q3 (percentile 0.75) avec series.quantile()
    # 2. Calcule iqr = q3 - q1
    # 3. Calcule lower_bound et upper_bound
    # -------------------------------------------------------------------------
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1

    lower_bound = round(q1 - (factor * iqr), 2)
    upper_bound = round(q3 + (factor * iqr), 2)

    outlier_mask = (series < lower_bound) | (series > upper_bound)
    outlier_indices = series[outlier_mask].index.tolist()

    return {
        "method": "IQR",
        "column": column,
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": len(outlier_indices),
        "outlier_indices": outlier_indices
    }


def hybrid_anomaly_scan(df: pd.DataFrame, source_type: str) -> List[Dict[str, Any]]:
    """
    Scanne un dataset selon sa source en combinant règles déterministes et statistiques.
    """
    anomalies = []
    source = source_type.upper()

    if source == "VMS":
        if "speed" in df.columns:
            speed_s = pd.to_numeric(df["speed"], errors="coerce")
            crit_speed = df[speed_s > 35.0]
            for idx, row in crit_speed.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("vessel_id", "")),
                    "rule": "DETERMINISTIC_MAX_SPEED_EXCEEDED",
                    "method": "DETERMINISTIC",
                    "severity": "CRITICAL",
                    "message": f"Vitesse impossible de {row['speed']} nœuds"
                })

        iqr_speed = detect_outliers_iqr(df, "speed", factor=1.5)
        crit_indices = set(a["row_index"] for a in anomalies)
        for idx in iqr_speed["outlier_indices"]:
            if idx not in crit_indices:
                val = df.loc[idx, "speed"]
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(df.loc[idx].get("vessel_id", "")),
                    "rule": "STATISTICAL_IQR_SPEED_OUTLIER",
                    "method": "IQR",
                    "severity": "WARNING",
                    "message": f"Vitesse inhabituelle de {val} nœuds (borne max IQR: {iqr_speed['upper_bound']})"
                })

    elif source == "ENV":
        if "sea_surface_temp" in df.columns:
            sst = pd.to_numeric(df["sea_surface_temp"], errors="coerce")
            bad_temp = df[(sst < 10.0) | (sst > 30.0)]
            for idx, row in bad_temp.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("sensor_id", "")),
                    "rule": "DETERMINISTIC_SST_PHYSICAL_RANGE",
                    "method": "DETERMINISTIC",
                    "severity": "CRITICAL",
                    "message": f"Température impossible : {row['sea_surface_temp']}°C"
                })

        sst_zscore = detect_outliers_zscore(df, "sea_surface_temp", threshold=3.0)
        crit_indices = set(a["row_index"] for a in anomalies)
        for idx in sst_zscore["outlier_indices"]:
            if idx not in crit_indices:
                row = df.loc[idx]
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("sensor_id", "")),
                    "rule": "STATISTICAL_ZSCORE_TEMP_DRIFT",
                    "method": "Z_SCORE",
                    "severity": "WARNING",
                    "message": f"Dérive thermique : {row['sea_surface_temp']}°C (Z > 3.0)"
                })

    return anomalies


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Détecteur Hybride (Branche dev-chaimae)")
    print("=" * 65)

    df_test_env = pd.DataFrame({
        "sensor_id": ["B-1"] * 7,
        "sea_surface_temp": [18.0, 18.2, 18.1, 17.9, 18.0, 18.1, 35.0]  # 35.0 est un outlier Z-Score
    })

    res_z = detect_outliers_zscore(df_test_env, "sea_surface_temp", threshold=2.0)
    print(f"Test Z-Score : {res_z['outlier_count']} anomalie(s) détectée(s) (Attendu : 1)")

    if res_z['outlier_count'] == 1:
        print("\n🎉 BRAVO CHAIMAE ! Tu as validé la détection statistique avec succès !")
        print("👉 Enregistre ton travail avec Git :")
        print("   git add .")
        print("   git commit -m \"Validation du detecteur d'anomalies hybride\"")
        print("   git push origin dev-chaimae")
    else:
        print("\n⏳ Le code attend d'être complété dans le TODO 1 (calcul du Z-Score) !")
        print("💡 Aide : Regarde la branche main si tu as besoin d'une inspiration.")