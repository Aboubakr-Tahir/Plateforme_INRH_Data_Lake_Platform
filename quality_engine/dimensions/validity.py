"""
Dimension 2 : Validité (Validity)
Mesure la conformité des données par rapport à un domaine de définition,
un format de données ou des règles physiques/géographiques métier.
Exemples INRH :
- Coordonnées GPS dans les eaux marocaines (Atlantique / Méditerranée)
- Vitesse d'un navire entre 0 et 35 nœuds
- Prix au kilo > 0
"""

from typing import Dict, Any, List
import pandas as pd


def check_range_validity(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> Dict[str, Any]:
    """Vérifie si les valeurs numériques d'une colonne respectent un intervalle [min_val, max_val]."""
    if column not in df.columns or df.empty:
        return {"score": 0.0, "invalid_rows_indices": []}

    series = pd.to_numeric(df[column], errors="coerce")
    valid_mask = series.between(min_val, max_val)
    invalid_indices = df[~valid_mask & series.notna()].index.tolist()

    valid_count = valid_mask.sum()
    total_non_null = series.notna().sum()

    score = round((valid_count / total_non_null * 100.0), 2) if total_non_null > 0 else 0.0

    return {
        "score": score,
        "invalid_count": len(invalid_indices),
        "invalid_indices": invalid_indices
    }


def check_maritime_coordinates(df: pd.DataFrame, lat_col="latitude", lon_col="longitude") -> Dict[str, Any]:
    """
    Vérifie si les coordonnées GPS se situent dans la Zone Économique Exclusive (ZEE) marocaine :
    - Latitude : 20.5°N à 36.0°N
    - Longitude : -18.0°W à -1.0°W
    """
    if lat_col not in df.columns or lon_col not in df.columns or df.empty:
        return {"score": 0.0, "invalid_count": 0, "invalid_indices": []}

    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")

    # Bounding box maritime Maroc
    valid_mask = (lat >= 20.5) & (lat <= 36.0) & (lon >= -18.0) & (lon <= -1.0)
    invalid_mask = (~valid_mask) & lat.notna() & lon.notna()
    invalid_indices = df[invalid_mask].index.tolist()

    total_valid = valid_mask.sum()
    total_evaluated = (lat.notna() & lon.notna()).sum()
    score = round((total_valid / total_evaluated * 100.0), 2) if total_evaluated > 0 else 0.0

    return {
        "score": score,
        "invalid_count": len(invalid_indices),
        "invalid_indices": invalid_indices
    }
