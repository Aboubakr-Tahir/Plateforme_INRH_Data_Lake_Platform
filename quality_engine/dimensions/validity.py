"""
Dimension 2 : Validité (Validity)
Mesure la conformité des données par rapport à un domaine de définition,
un format de données ou des règles physiques et géographiques métier.

Exemples INRH :
- Coordonnées GPS dans les eaux marocaines (Atlantique / Méditerranée)
- Vitesse d'un navire entre 0.0 et 35.0 nœuds
- Prix total et quantité strictement positifs (> 0)

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/dimensions/validity.py
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

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # Crée un masque booléen 'valid_mask' qui vaut True si la valeur est comprise
    # entre min_val et max_val inclus.
    # Indice : utilise series.between(min_val, max_val) ou (series >= min_val) & (series <= max_val)
    # -------------------------------------------------------------------------
    valid_mask = None  # Remplace par ton code (ex: series.between(min_val, max_val))

    if valid_mask is None:
        return {"score": 0.0, "valid_count": 0, "invalid_count": 0, "invalid_indices": []}

    valid_mask = valid_mask & non_null_mask
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
    Vérifie si les coordonnées GPS se situent dans le domaine maritime marocain.
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

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 2/2 :
    # Définis le masque 'in_morocco_box' pour vérifier que la latitude et la longitude
    # sont dans les eaux marocaines :
    # - lat >= MAROC_LAT_MIN (20.5) et lat <= MAROC_LAT_MAX (36.0)
    # - lon >= MAROC_LON_MIN (-18.0) et lon <= MAROC_LON_MAX (-1.0)
    # -------------------------------------------------------------------------
    in_morocco_box = None  # Remplace par ton code avec des & entre les 4 conditions

    if in_morocco_box is None:
        return {"score": 0.0, "valid_count": 0, "invalid_count": 0, "invalid_indices": []}

    # Détection des points tombant sur la terre ferme (Atlas/désert intérieur)
    on_land_east = (lat >= 28.0) & (lat <= 34.0) & (lon > -7.0)

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
    Applique l'ensemble des règles de validité selon la source.
    """
    source = source_type.upper()
    rules_results = []
    all_invalid_indices = set()

    if source == "VMS":
        res_speed = check_numeric_range(df, "speed", min_val=0.0, max_val=35.0)
        rules_results.append(res_speed)
        all_invalid_indices.update(res_speed["invalid_indices"])

        res_geo = check_maritime_coordinates(df, "latitude", "longitude")
        rules_results.append(res_geo)
        all_invalid_indices.update(res_geo["invalid_indices"])

    elif source == "SALES":
        res_price = check_numeric_range(df, "total_price", min_val=0.01, max_val=10_000_000.0)
        rules_results.append(res_price)
        all_invalid_indices.update(res_price["invalid_indices"])

        res_qty = check_numeric_range(df, "quantity_kg", min_val=0.1, max_val=500_000.0)
        rules_results.append(res_qty)
        all_invalid_indices.update(res_qty["invalid_indices"])

    elif source == "LOGBOOK":
        res_weight = check_numeric_range(df, "weight_kg", min_val=0.1, max_val=500_000.0)
        rules_results.append(res_weight)
        all_invalid_indices.update(res_weight["invalid_indices"])

        res_geo = check_maritime_coordinates(df, "latitude", "longitude")
        rules_results.append(res_geo)
        all_invalid_indices.update(res_geo["invalid_indices"])

    elif source == "ENV":
        res_temp = check_numeric_range(df, "sea_surface_temp", min_val=10.0, max_val=30.0)
        rules_results.append(res_temp)
        all_invalid_indices.update(res_temp["invalid_indices"])

    if not rules_results:
        return {"score": 100.0, "rules": [], "total_invalid": 0, "invalid_indices": []}

    avg_score = sum(r["score"] for r in rules_results) / len(rules_results)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "rules": rules_results,
        "total_invalid": len(all_invalid_indices),
        "invalid_indices": sorted(list(all_invalid_indices))
    }


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Dimension Validité (Branche dev-chaimae)")
    print("=" * 65)

    # Petit jeu de test
    df_test_vms = pd.DataFrame({
        "speed": [12.0, 30.0, 150.0, -5.0],      # 2 valides sur 4 (12 et 30) = 50%
        "latitude": [30.4, 25.0, 31.8, 45.0],    # 45 = hors Maroc, 31.8 = terre ferme
        "longitude": [-9.7, -15.0, -6.2, -10.0]
    })

    res_speed = check_numeric_range(df_test_vms, "speed", 0.0, 35.0)
    res_geo = check_maritime_coordinates(df_test_vms)

    print(f"Test Vitesse (0-35 nœuds) : {res_speed['score']}% (Attendu : 50.0%)")
    print(f"Test GPS Eaux Marocaines  : {res_geo['score']}% (Attendu : 50.0%)")

    if res_speed['score'] == 50.0 and res_geo['score'] == 50.0:
        print("\n🎉 BRAVO CHAIMAE ! Tu as validé la dimension Validité avec succès !")
        print("👉 Enregistre ton travail avec Git :")
        print("   git add .")
        print("   git commit -m \"Validation de la dimension validité\"")
        print("   git push origin dev-chaimae")
    else:
        print("\n⏳ Le code attend d'être complété dans les TODO 1 et 2 !")
        print("💡 Aide : Si tu as un doute, regarde le code de référence sur la branche main.")