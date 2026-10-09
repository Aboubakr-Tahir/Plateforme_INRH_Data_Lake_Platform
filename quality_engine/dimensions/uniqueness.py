"""
Dimension 3 : Unicité (Uniqueness)
Mesure l'absence de redondance et de doublons dans le jeu de données.

Norme DAMA International :
Deux niveaux d'évaluation :
1. Doublons stricts : lignes entièrement identiques sur toutes les colonnes.
2. Doublons de clé : plusieurs lignes partageant la même clé primaire (PK)
   ou la même clé métier composite (ex: même navire au même timestamp).

Formule : Unicité (%) = (Total lignes - Nombre de doublons) / (Total lignes) * 100

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/dimensions/uniqueness.py
"""

import os
from typing import Dict, Any, List, Union
import pandas as pd


# Référentiel des clés métier et primaires par source INRH
SOURCE_KEYS = {
    "VMS": {
        "primary_key": "vms_id",
        "business_key": ["vessel_id", "timestamp"]
    },
    "LOGBOOK": {
        "primary_key": "log_id",
        "business_key": ["trip_id", "species_code"]
    },
    "SALES": {
        "primary_key": "sale_id",
        "business_key": ["trip_id", "species_code"]
    },
    "ENV": {
        "primary_key": "env_id",
        "business_key": ["sensor_id", "timestamp"]
    }
}


def check_uniqueness_on_columns(
    df: pd.DataFrame,
    subset_columns: Union[str, List[str]] = None,
    rule_name: str = "STRICT_DUPLICATES"
) -> Dict[str, Any]:
    """
    Vérifie l'unicité sur un ensemble de colonnes données.
    Si subset_columns=None, vérifie les doublons stricts sur toutes les colonnes.
    """
    if df.empty:
        return {
            "rule_name": rule_name,
            "score": 100.0,
            "total_rows": 0,
            "duplicate_count": 0,
            "duplicate_indices": []
        }

    total_rows = len(df)
    cols = [subset_columns] if isinstance(subset_columns, str) else subset_columns

    if cols is not None:
        existing_cols = [c for c in cols if c in df.columns]
        if not existing_cols:
            return {
                "rule_name": rule_name,
                "score": 100.0,
                "total_rows": total_rows,
                "duplicate_count": 0,
                "duplicate_indices": []
            }
        cols = existing_cols

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # 1. Utilise la fonction .duplicated() de Pandas sur le DataFrame pour créer
    #    un masque booléen qui marque les lignes en doublon.
    #    Indice : df.duplicated(subset=cols, keep="first")
    # -------------------------------------------------------------------------
    duplicate_mask = None  # Remplace par ton code (ex: df.duplicated(subset=cols, keep="first"))

    if duplicate_mask is None:
        return {
            "rule_name": rule_name,
            "score": 0.0,
            "total_rows": total_rows,
            "duplicate_count": 0,
            "duplicate_indices": []
        }

    duplicate_indices = df[duplicate_mask].index.tolist()
    duplicate_count = len(duplicate_indices)

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 2/2 :
    # 2. Calcule le score d'unicité en pourcentage :
    #    Formule : (total_rows - duplicate_count) / total_rows * 100
    # -------------------------------------------------------------------------
    score = None  # Remplace par la formule de calcul du pourcentage

    if score is None:
        return {
            "rule_name": rule_name,
            "score": 0.0,
            "total_rows": total_rows,
            "duplicate_count": duplicate_count,
            "duplicate_indices": duplicate_indices
        }

    return {
        "rule_name": rule_name,
        "score": round(float(score), 2),
        "total_rows": total_rows,
        "duplicate_count": duplicate_count,
        "duplicate_indices": duplicate_indices
    }


def evaluate_source_uniqueness(df: pd.DataFrame, source_type: str) -> Dict[str, Any]:
    """
    Évalue l'unicité complète d'un jeu de données selon sa source.
    """
    source = source_type.upper()
    keys_config = SOURCE_KEYS.get(source, {})
    rules_results = []
    all_duplicate_indices = set()

    # 1. Doublons stricts (toutes colonnes)
    strict_res = check_uniqueness_on_columns(
        df,
        subset_columns=None,
        rule_name="STRICT_FULL_ROW_DUPLICATES"
    )
    rules_results.append(strict_res)
    all_duplicate_indices.update(strict_res["duplicate_indices"])

    # 2. Clé primaire
    pk = keys_config.get("primary_key")
    if pk and pk in df.columns:
        pk_res = check_uniqueness_on_columns(
            df,
            subset_columns=pk,
            rule_name=f"PRIMARY_KEY_UNIQUENESS_[{pk}]"
        )
        rules_results.append(pk_res)
        all_duplicate_indices.update(pk_res["duplicate_indices"])

    # 3. Clé métier composite
    bk = keys_config.get("business_key")
    if bk and all(col in df.columns for col in bk):
        bk_res = check_uniqueness_on_columns(
            df,
            subset_columns=bk,
            rule_name=f"BUSINESS_KEY_UNIQUENESS_[{'+'.join(bk)}]"
        )
        rules_results.append(bk_res)
        all_duplicate_indices.update(bk_res["duplicate_indices"])

    avg_score = sum(r["score"] for r in rules_results) / len(rules_results)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "rules": rules_results,
        "total_duplicates": len(all_duplicate_indices),
        "duplicate_indices": sorted(list(all_duplicate_indices))
    }


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Dimension Unicité (Branche dev-chaimae)")
    print("=" * 65)

    # Petit DataFrame de test avec un doublon strict et un doublon de clé
    df_test = pd.DataFrame({
        "vessel_id": ["MAR-01", "MAR-02", "MAR-01", "MAR-01"],
        "timestamp": ["10:00",  "10:00",  "10:00",  "10:00"],  # Ligne 2 et 3 sont des doublons de (vessel, timestamp)
        "speed":     [12.0,     15.0,     12.0,     8.0]       # Ligne 2 est un doublon strict de la ligne 0
    })

    res_strict = check_uniqueness_on_columns(df_test, subset_columns=None)
    res_key = check_uniqueness_on_columns(df_test, subset_columns=["vessel_id", "timestamp"])

    print(f"Test Doublons Stricts : {res_strict['score']}% (Attendu : 75.0%)")
    print(f"Test Clé Composite    : {res_key['score']}% (Attendu : 50.0%)")

    if res_strict['score'] == 75.0 and res_key['score'] == 50.0:
        print("\n🎉 BRAVO CHAIMAE ! Tu as validé la dimension Unicité avec succès !")
        print("👉 Enregistre ton travail avec Git :")
        print("   git add .")
        print("   git commit -m \"Validation de la dimension unicité\"")
        print("   git push origin dev-chaimae")
    else:
        print("\n⏳ Le code attend d'être complété dans les TODO 1 et 2 !")
        print("💡 Aide : Si tu as un doute, regarde le code de référence sur la branche main.")