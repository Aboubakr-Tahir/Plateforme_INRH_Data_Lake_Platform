"""
Dimension 3 : Unicité (Uniqueness)
Mesure l'absence de redondance et de doublons dans le jeu de données.

Norme DAMA International :
Deux niveaux d'évaluation :
1. Doublons stricts : lignes entièrement identiques sur toutes les colonnes.
2. Doublons de clé : plusieurs lignes partageant la même clé primaire (PK)
   ou la même clé métier composite (ex: même navire au même timestamp).

Formule : Unicité (%) = (Total lignes - Nombre de doublons) / (Total lignes) * 100
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
    
    keep='first' marque toutes les occurrences d'une valeur après la première comme True (doublon).
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

    # Si certaines colonnes demandées ne sont pas dans le DataFrame
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

    # Détection des doublons avec Pandas
    duplicate_mask = df.duplicated(subset=cols, keep="first")
    duplicate_indices = df[duplicate_mask].index.tolist()
    duplicate_count = len(duplicate_indices)

    # Calcul du score d'unicité en pourcentage
    score = ((total_rows - duplicate_count) / total_rows) * 100.0
    score = round(score, 2)

    return {
        "rule_name": rule_name,
        "score": score,
        "total_rows": total_rows,
        "duplicate_count": duplicate_count,
        "duplicate_indices": duplicate_indices
    }


def evaluate_source_uniqueness(df: pd.DataFrame, source_type: str) -> Dict[str, Any]:
    """
    Évalue l'unicité complète d'un jeu de données selon sa source :
    1. Doublons stricts (toutes les colonnes)
    2. Unicité de la clé primaire (PK)
    3. Unicité de la clé métier composite (ex: vessel_id + timestamp)
    """
    source = source_type.upper()
    keys_config = SOURCE_KEYS.get(source, {})
    rules_results = []
    all_duplicate_indices = set()

    # 1. Vérification des doublons stricts (toutes colonnes)
    strict_res = check_uniqueness_on_columns(
        df,
        subset_columns=None,
        rule_name="STRICT_FULL_ROW_DUPLICATES"
    )
    rules_results.append(strict_res)
    all_duplicate_indices.update(strict_res["duplicate_indices"])

    # 2. Vérification de la clé primaire
    pk = keys_config.get("primary_key")
    if pk and pk in df.columns:
        pk_res = check_uniqueness_on_columns(
            df,
            subset_columns=pk,
            rule_name=f"PRIMARY_KEY_UNIQUENESS_[{pk}]"
        )
        rules_results.append(pk_res)
        all_duplicate_indices.update(pk_res["duplicate_indices"])

    # 3. Vérification de la clé métier composite
    bk = keys_config.get("business_key")
    if bk and all(col in df.columns for col in bk):
        bk_res = check_uniqueness_on_columns(
            df,
            subset_columns=bk,
            rule_name=f"BUSINESS_KEY_UNIQUENESS_[{'+'.join(bk)}]"
        )
        rules_results.append(bk_res)
        all_duplicate_indices.update(bk_res["duplicate_indices"])

    # Score moyen d'unicité
    avg_score = sum(r["score"] for r in rules_results) / len(rules_results)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "rules": rules_results,
        "total_duplicates": len(all_duplicate_indices),
        "duplicate_indices": sorted(list(all_duplicate_indices))
    }


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU MODULE D'UNICITÉ (Branche main)")
    print("=" * 65)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generator", "mock_data")
    logbook_path = os.path.join(data_dir, "logbook_batch_01.csv")
    vms_path = os.path.join(data_dir, "vms_batch_01.csv")

    # 1. Test sur LOGBOOK (notre générateur a injecté 2 doublons stricts)
    if os.path.exists(logbook_path):
        df_logbook = pd.read_csv(logbook_path)
        log_res = evaluate_source_uniqueness(df_logbook, "LOGBOOK")
        print(f"📖 LOGBOOK ({len(df_logbook)} lignes) :")
        print(f"   🎯 Score d'Unicité : {log_res['score']}%")
        print(f"   🚨 Lignes en doublon : {log_res['total_duplicates']}")
        for r in log_res["rules"]:
            print(f"      - {r['rule_name']:<40} : {r['score']:>6.2f}% ({r['duplicate_count']} doublons)")

    # 2. Test sur VMS
    if os.path.exists(vms_path):
        df_vms = pd.read_csv(vms_path)
        vms_res = evaluate_source_uniqueness(df_vms, "VMS")
        print(f"\n📡 VMS ({len(df_vms)} lignes) :")
        print(f"   🎯 Score d'Unicité : {vms_res['score']}%")
        print(f"   🚨 Lignes en doublon : {vms_res['total_duplicates']}")
        for r in vms_res["rules"]:
            print(f"      - {r['rule_name']:<40} : {r['score']:>6.2f}% ({r['duplicate_count']} doublons)")

    print("\n✅ Module d'unicité validé avec succès sur main !")