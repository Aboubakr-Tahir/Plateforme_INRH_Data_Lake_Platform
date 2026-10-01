"""
Module de Détection d'Anomalies Hybride :
Combine :
1. Méthodes Déterministes (Règles métier fixes et seuils physiques)
2. Méthodes Statistiques (Z-Score et IQR - Interquartile Range)
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def detect_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> Dict[str, Any]:
    """
    Détecte les anomalies statistiques via le Z-score.
    Z = (x - moyenne) / ecart_type
    Une valeur est anormale si |Z| > threshold (standard: 3.0).
    """
    if column not in df.columns or df.empty:
        return {"outliers_count": 0, "indices": []}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 3:
        return {"outliers_count": 0, "indices": []}

    mean = series.mean()
    std = series.std()

    if std == 0 or np.isnan(std):
        return {"outliers_count": 0, "indices": []}

    z_scores = (series - mean).abs() / std
    outliers_mask = z_scores > threshold
    outlier_indices = series[outliers_mask].index.tolist()

    return {
        "method": "Z-SCORE",
        "column": column,
        "mean": round(float(mean), 2),
        "std": round(float(std), 2),
        "threshold": threshold,
        "outliers_count": len(outlier_indices),
        "indices": outlier_indices
    }


def detect_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 1.5) -> Dict[str, Any]:
    """
    Détecte les anomalies statistiques via la boîte à moustaches (IQR).
    Q1 = 25ème percentile, Q3 = 75ème percentile
    IQR = Q3 - Q1
    Borne inférieure = Q1 - factor * IQR
    Borne supérieure = Q3 + factor * IQR
    Très robuste contre les distributions asymétriques.
    """
    if column not in df.columns or df.empty:
        return {"outliers_count": 0, "indices": []}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 4:
        return {"outliers_count": 0, "indices": []}

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - (factor * iqr)
    upper_bound = q3 + (factor * iqr)

    outliers_mask = (series < lower_bound) | (series > upper_bound)
    outlier_indices = series[outliers_mask].index.tolist()

    return {
        "method": "IQR",
        "column": column,
        "q1": round(float(q1), 2),
        "q3": round(float(q3), 2),
        "iqr": round(float(iqr), 2),
        "lower_bound": round(float(lower_bound), 2),
        "upper_bound": round(float(upper_bound), 2),
        "outliers_count": len(outlier_indices),
        "indices": outlier_indices
    }


def hybrid_anomaly_scan(df: pd.DataFrame, source_type: str) -> List[Dict[str, Any]]:
    """
    Scanne un DataFrame selon son type de source (VMS, LOGBOOK, SALES, ENV)
    en combinant règles métier et méthodes statistiques.
    Retourne la liste des anomalies trouvées avec leur niveau de sévérité (CRITICAL, WARNING).
    """
    anomalies = []
    source = source_type.upper()

    if source == "VMS":
        # 1. Règle métier : Vitesse supérieure à 35 nœuds
        if "speed_knots" in df.columns:
            high_speed = df[pd.to_numeric(df["speed_knots"], errors="coerce") > 35]
            for idx, row in high_speed.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("vessel_id", "")),
                    "rule": "VMS_MAX_SPEED_EXCEEDED",
                    "severity": "CRITICAL",
                    "message": f"Vitesse anormale de {row['speed_knots']} nœuds (max chalutier: 35 nœuds)"
                })

        # 2. Règle statistique : Détection IQR sur la vitesse
        iqr_res = detect_outliers_iqr(df, "speed_knots")
        for idx in iqr_res["indices"]:
            if idx not in [a["row_index"] for a in anomalies]:
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(df.loc[idx].get("vessel_id", "")),
                    "rule": "VMS_STATISTICAL_SPEED_OUTLIER",
                    "severity": "WARNING",
                    "message": f"Vitesse inhabituelle détectée par méthode IQR"
                })

    elif source == "ENV":
        # Règle physique : Température de l'eau dans l'Atlantique marocain (hors 10°C - 30°C)
        if "water_temp_celsius" in df.columns:
            temp = pd.to_numeric(df["water_temp_celsius"], errors="coerce")
            bad_temp = df[(temp < 10.0) | (temp > 30.0)]
            for idx, row in bad_temp.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("buoy_id", "")),
                    "rule": "ENV_TEMP_RANGE_ERROR",
                    "severity": "CRITICAL",
                    "message": f"Température impossible pour l'Atlantique : {row['water_temp_celsius']}°C"
                })

    elif source == "SALES":
        # Règle financière : Prix négatif ou nul
        if "price_mad_per_kg" in df.columns:
            price = pd.to_numeric(df["price_mad_per_kg"], errors="coerce")
            bad_price = df[price <= 0]
            for idx, row in bad_price.iterrows():
                anomalies.append({
                    "row_index": idx,
                    "entity_id": str(row.get("sale_id", "")),
                    "rule": "SALES_INVALID_PRICE",
                    "severity": "CRITICAL",
                    "message": f"Prix de vente invalide ou négatif : {row['price_mad_per_kg']} MAD"
                })

    return anomalies
