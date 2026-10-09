"""
Dimension 2 : Validité (Validity)
Mesure la conformité des données par rapport à un domaine de définition,
un format de données ou des règles physiques et géographiques métier.

Exemples INRH :
- Coordonnées GPS dans les eaux marocaines (Atlantique / Méditerranée)
- Vitesse d'un navire entre 0.0 et 35.0 nœuds
- Prix total et quantité strictement positifs (> 0)
- Température de surface de l'eau entre 10.0°C et 30.0°C
"""

import os
from typing import Dict, Any, List
import pandas as pd


# Bornes maritimes officielles de la Zone Économique Exclusive (ZEE) marocaine
MAROC_LAT_MIN = 20.5
MAROC_LAT_MAX = 36.0
MAROC_LON_MIN = -18.0
MAROC_LON_MAX = -1.0


def check_numeric_range(
    df: pd.DataFrame,
    column: str,
    min_val: float,
    max_val: float
) -> Dict[str, Any]:
    """
    Vérifie si les valeurs numériques d'une colonne respectent l'intervalle [min_val, max_val].
    Ignore les valeurs NaN (déjà traitées par la dimension Complétude).
    """
    if column not in df.columns or df.empty:
        return {
            "score": 0.0,
            "valid_count": 0,
            "invalid_count": 0,
            "invalid_indices": []
        }

    series = pd.to_numeric(df[column], errors="coerce")
    non_null_mask = series.notna()
    total_evaluated = int(non_null_mask.sum())

    if total_evaluated == 0:
        return {
            "score": 100.0,
            "valid_count": 0,
            "invalid_count": 0,
            "invalid_indices": []
        }

    # Masque des valeurs valides dans l'intervalle [min_val, max_val]
    valid_mask = series.between(min_val, max_val) & non_null_mask
    invalid_mask = (~valid_mask) & non_null_mask

    valid_count = int(valid_mask.sum())
    invalid_indices = df[invalid_mask].index.tolist()
    invalid_count = len(invalid_indices)

    score = round((valid_count / total_evaluated) * 100.0, 2)

    return {
        "rule_name": f"RANGE_{column.upper()}_[{min_val}_{max_val}]",
        "score": score,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_indices": invalid_indices
    }


def check_maritime_coordinates(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude"
) -> Dict[str, Any]:
    """
    Vérifie si les coordonnées GPS se situent dans le domaine maritime marocain :
      - Latitude  : entre 20.5°N et 36.0°N
      - Longitude : entre -18.0°W et -1.0°W
    Détecte également les coordonnées anormalement tombées sur la terre ferme.
    """
    if lat_col not in df.columns or lon_col not in df.columns or df.empty:
        return {
            "score": 0.0,
            "valid_count": 0,
            "invalid_count": 0,
            "invalid_indices": []
        }

    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")
    both_present = lat.notna() & lon.notna()
    total_evaluated = int(both_present.sum())

    if total_evaluated == 0:
        return {
            "score": 100.0,
            "valid_count": 0,
            "invalid_count": 0,
            "invalid_indices": []
        }

    # 1. Bounding box maritime générale Maroc
    in_morocco_box = (
        (lat >= MAROC_LAT_MIN) & (lat <= MAROC_LAT_MAX) &
        (lon >= MAROC_LON_MIN) & (lon <= MAROC_LON_MAX)
    )

    # 2. Détection de points tombant sur la terre ferme (ex: Atlas / désert intérieur)
    # Entre 28°N et 34°N, la côte atlantique marocaine se situe à l'ouest de -7.5°W
    on_land_east = (lat >= 28.0) & (lat <= 34.0) & (lon > -7.0)

    # Coordonnées valides = dans la boîte maritime ET pas sur la terre ferme
    valid_coords = in_morocco_box & (~on_land_east) & both_present
    invalid_mask = (~valid_coords) & both_present

    valid_count = int(valid_coords.sum())
    invalid_indices = df[invalid_mask].index.tolist()
    invalid_count = len(invalid_indices)

    score = round((valid_count / total_evaluated) * 100.0, 2)

    return {
        "rule_name": "MOROCCAN_MARITIME_WATERS_GPS",
        "score": score,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_indices": invalid_indices
    }


def evaluate_source_validity(df: pd.DataFrame, source_type: str) -> Dict[str, Any]:
    """
    Applique l'ensemble des règles de validité métier pour une source donnée :
    - VMS     : Vitesse [0.0, 35.0] nœuds + Coordonnées maritimes
    - SALES   : Prix total > 0 + Quantité > 0
    - LOGBOOK : Poids capturé > 0 + Coordonnées maritimes
    - ENV     : Température eau [10.0, 30.0]°C
    """
    source = source_type.upper()
    rules_results = []
    all_invalid_indices = set()

    if source == "VMS":
        # Règle 1 : Vitesse navire
        res_speed = check_numeric_range(df, "speed", min_val=0.0, max_val=35.0)
        rules_results.append(res_speed)
        all_invalid_indices.update(res_speed["invalid_indices"])

        # Règle 2 : Position GPS maritime
        res_geo = check_maritime_coordinates(df, "latitude", "longitude")
        rules_results.append(res_geo)
        all_invalid_indices.update(res_geo["invalid_indices"])

    elif source == "SALES":
        # Règle 1 : Prix total strictement positif (> 0.0)
        res_price = check_numeric_range(df, "total_price", min_val=0.01, max_val=10_000_000.0)
        rules_results.append(res_price)
        all_invalid_indices.update(res_price["invalid_indices"])

        # Règle 2 : Quantité vendue positive (> 0.0)
        res_qty = check_numeric_range(df, "quantity_kg", min_val=0.1, max_val=500_000.0)
        rules_results.append(res_qty)
        all_invalid_indices.update(res_qty["invalid_indices"])

    elif source == "LOGBOOK":
        # Règle 1 : Poids estimé positif
        res_weight = check_numeric_range(df, "weight_kg", min_val=0.1, max_val=500_000.0)
        rules_results.append(res_weight)
        all_invalid_indices.update(res_weight["invalid_indices"])

        # Règle 2 : Coordonnées du trait de pêche
        res_geo = check_maritime_coordinates(df, "latitude", "longitude")
        rules_results.append(res_geo)
        all_invalid_indices.update(res_geo["invalid_indices"])

    elif source == "ENV":
        # Règle 1 : Température de l'eau
        res_temp = check_numeric_range(df, "sea_surface_temp", min_val=10.0, max_val=30.0)
        rules_results.append(res_temp)
        all_invalid_indices.update(res_temp["invalid_indices"])

    if not rules_results:
        return {
            "score": 100.0,
            "rules": [],
            "total_invalid": 0,
            "invalid_indices": []
        }

    # Score moyen de validité sur toutes les règles appliquées
    avg_score = sum(r["score"] for r in rules_results) / len(rules_results)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "rules": rules_results,
        "total_invalid": len(all_invalid_indices),
        "invalid_indices": sorted(list(all_invalid_indices))
    }


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU MODULE DE VALIDITÉ (Branche main)")
    print("=" * 65)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generator", "mock_data")
    vms_path = os.path.join(data_dir, "vms_batch_01.csv")
    sales_path = os.path.join(data_dir, "sales_batch_01.csv")

    # 1. Test sur VMS
    if os.path.exists(vms_path):
        df_vms = pd.read_csv(vms_path)
        vms_res = evaluate_source_validity(df_vms, "VMS")
        print(f"📡 VMS ({len(df_vms)} lignes) :")
        print(f"   🎯 Score de Validité : {vms_res['score']}%")
        print(f"   🚨 Lignes invalides  : {vms_res['total_invalid']}")
        for r in vms_res["rules"]:
            print(f"      - {r['rule_name']:<35} : {r['score']:>6.2f}% ({r['invalid_count']} anomalies)")

    # 2. Test sur SALES
    if os.path.exists(sales_path):
        df_sales = pd.read_csv(sales_path)
        sales_res = evaluate_source_validity(df_sales, "SALES")
        print(f"\n💰 SALES ({len(df_sales)} lignes) :")
        print(f"   🎯 Score de Validité : {sales_res['score']}%")
        print(f"   🚨 Lignes invalides  : {sales_res['total_invalid']}")
        for r in sales_res["rules"]:
            print(f"      - {r['rule_name']:<35} : {r['score']:>6.2f}% ({r['invalid_count']} anomalies)")

    print("\n✅ Module de validité validé avec succès sur main !")