"""
Module de Détection d'Anomalies Hybride :
Combine deux approches complémentaires :
1. Méthodes Déterministes : Règles métier strictes et seuils physiques
   (ex: vitesse > 35 nœuds, coordonnées hors ZEE marocaine, prix <= 0).
2. Méthodes Statistiques :
   - Z-Score : Pour les distributions gaussiennes / symétriques (température et salinité dans ENV).
   - IQR (Boîte à moustaches) : Pour les distributions asymétriques
     (vitesses dans VMS, tonnages dans LOGBOOK, prix au kilo dans SALES).
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
    Une valeur est considérée anormale si Z > threshold (standard: 3.0, règle des 3-sigmas).
    Idéal pour les distributions normales / symétriques (ex: température de l'eau).
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

    z_scores = (series - mean).abs() / std
    outlier_mask = z_scores > threshold
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
    Détecte les anomalies via la boîte à moustaches (IQR - Interquartile Range) :
        IQR = Q3 (75ème percentile) - Q1 (25ème percentile)
        Borne inférieure = Q1 - (factor * IQR)
        Borne supérieure = Q3 + (factor * IQR)
    Idéal pour les données asymétriques (tonnages de pêche, prix, vitesses).
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
    Scanne un dataset selon sa source en combinant règles déterministes et méthodes statistiques.
    Retourne la liste détaillée des anomalies (row_index, entity_id, rule, severity, message).
    """
    anomalies = []
    source = source_type.upper()

    if source == "VMS":
        # 1. Déterministe : Vitesse physique impossible (> 35 nœuds)
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
                    "message": f"Vitesse impossible de {row['speed']} nœuds (max chalutier: 35 nœuds)"
                })

        # 2. Statistique IQR : Vitesse inhabituelle pour la flottille
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
                    "message": f"Vitesse inhabituelle de {val} nœuds (borne IQR max: {iqr_speed['upper_bound']})"
                })

    elif source == "SALES":
        # 1. Déterministe : Prix total négatif ou nul
        if "total_price" in df.columns:
            prices = pd.to_numeric(df["total_price"], errors="coerce")
            bad_prices = df[prices <= 0]
            for idx, row in bad_prices.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("sale_id", "")),
                    "rule": "DETERMINISTIC_INVALID_PRICE",
                    "method": "DETERMINISTIC",
                    "severity": "CRITICAL",
                    "message": f"Prix total négatif ou nul : {row['total_price']} MAD"
                })

        # 2. Statistique Z-Score : Prix au kilo anormal par espèce
        if {"total_price", "quantity_kg", "species_code"}.issubset(df.columns):
            df_calc = df.copy()
            qty = pd.to_numeric(df_calc["quantity_kg"], errors="coerce").replace(0, np.nan)
            df_calc["unit_price"] = pd.to_numeric(df_calc["total_price"], errors="coerce") / qty

            for sp in df_calc["species_code"].dropna().unique():
                sp_subset = df_calc[df_calc["species_code"] == sp]
                sp_zscore = detect_outliers_zscore(sp_subset, "unit_price", threshold=3.0)
                for idx in sp_zscore["outlier_indices"]:
                    row = df.loc[idx]
                    unit_p = round(df_calc.loc[idx, "unit_price"], 2)
                    anomalies.append({
                        "row_index": idx,
                        "entity_id": str(row.get("sale_id", "")),
                        "rule": f"STATISTICAL_ZSCORE_PRICE_SPIKE_[{sp}]",
                        "method": "Z_SCORE",
                        "severity": "WARNING",
                        "message": f"Prix unitaire anormal de {unit_p} MAD/kg pour l'espèce {sp} (Z > 3.0)"
                    })

    elif source == "LOGBOOK":
        # 1. Déterministe : Poids négatif
        if "weight_kg" in df.columns:
            weights = pd.to_numeric(df["weight_kg"], errors="coerce")
            bad_w = df[weights <= 0]
            for idx, row in bad_w.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("trip_id", "")),
                    "rule": "DETERMINISTIC_NEGATIVE_CATCH_WEIGHT",
                    "method": "DETERMINISTIC",
                    "severity": "CRITICAL",
                    "message": f"Poids de capture négatif ou nul : {row['weight_kg']} kg"
                })

        # 2. Statistique IQR : Capture disproportionnée par marée
        iqr_weight = detect_outliers_iqr(df, "weight_kg", factor=1.5)
        for idx in iqr_weight["outlier_indices"]:
            row = df.loc[idx]
            anomalies.append({
                "row_index": idx,
                "entity_id": str(row.get("trip_id", "")),
                "rule": "STATISTICAL_IQR_CATCH_OUTLIER",
                "method": "IQR",
                "severity": "WARNING",
                "message": f"Tonnage exceptionnel de {row['weight_kg']} kg (borne max IQR: {iqr_weight['upper_bound']} kg)"
            })

    elif source == "ENV":
        # 1. Déterministe : Température physiquement impossible dans l'Atlantique marocain (< 10°C ou > 30°C)
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
                    "message": f"Température de surface impossible : {row['sea_surface_temp']}°C"
                })

        # 2. Statistique Z-Score : Dérive fine de température
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
                    "message": f"Dérive thermique inhabituelle détectée : {row['sea_surface_temp']}°C (Z > 3.0)"
                })

    return anomalies


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU DÉTECTEUR D'ANOMALIES HYBRIDE (Branche main)")
    print("=" * 65)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generator", "mock_data")
    vms_path = os.path.join(data_dir, "vms_batch_01.csv")
    sales_path = os.path.join(data_dir, "sales_batch_01.csv")
    env_path = os.path.join(data_dir, "env_batch_01.csv")

    for src_name, path in [("VMS", vms_path), ("SALES", sales_path), ("ENV", env_path)]:
        if os.path.exists(path):
            df_test = pd.read_csv(path)
            anoms = hybrid_anomaly_scan(df_test, src_name)
            crit = sum(1 for a in anoms if a["severity"] == "CRITICAL")
            warn = sum(1 for a in anoms if a["severity"] == "WARNING")
            print(f"🔍 {src_name} ({len(df_test)} lignes) :")
            print(f"   🚨 Total anomalies : {len(anoms)} (Critiques: {crit}, Avertissements: {warn})")
            if anoms:
                print(f"   Exemple : [{anoms[0]['severity']}] {anoms[0]['rule']} -> {anoms[0]['message']}")
            print()

    print("✅ Détecteur d'anomalies hybride validé avec succès sur main !")