"""
Dimension 4 : Cohérence (Consistency)
Vérifie la logique relationnelle et temporelle entre plusieurs colonnes ou plusieurs tables.

Norme DAMA International :
Deux types de contrôles fondamentaux :
1. Cohérence temporelle / chronologique :
   - La date de vente en criée (SALES.sale_date) doit être postérieure ou égale
     à la date de déclaration de marée (LOGBOOK.log_date).
2. Cohérence relationnelle croisée (Logbook vs Sales) :
   - Le tonnage vendu en criée doit correspondre au tonnage déclaré dans le Logbook.
   - Alerte Fraude / Sous-déclaration : Si quantity_kg (SALES) > 2.0 * weight_kg (LOGBOOK).

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/dimensions/consistency.py
"""

import os
from typing import Dict, Any, List
import pandas as pd


def check_sales_vs_logbook_chronology(
    logbook_df: pd.DataFrame,
    sales_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Vérifie que pour un même trip_id, la vente en criée (sale_date)
    a lieu le jour même ou après la déclaration de pêche (log_date).
    Règle : sale_date >= log_date
    """
    if "trip_id" not in logbook_df.columns or "trip_id" not in sales_df.columns:
        return {
            "rule_name": "TEMPORAL_CHRONOLOGY_LOGBOOK_VS_SALES",
            "score": 100.0,
            "total_evaluated": 0,
            "invalid_count": 0,
            "invalid_sales_ids": []
        }

    merged = pd.merge(
        sales_df[["sale_id", "trip_id", "sale_date"]],
        logbook_df[["trip_id", "log_date"]].drop_duplicates(subset=["trip_id"]),
        on="trip_id",
        how="inner"
    )

    if merged.empty:
        return {
            "rule_name": "TEMPORAL_CHRONOLOGY_LOGBOOK_VS_SALES",
            "score": 100.0,
            "total_evaluated": 0,
            "invalid_count": 0,
            "invalid_sales_ids": []
        }

    sale_dates = pd.to_datetime(merged["sale_date"], errors="coerce")
    log_dates = pd.to_datetime(merged["log_date"], errors="coerce")

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # Crée un masque booléen 'invalid_mask' pour détecter les ventes incohérentes :
    # Une vente est invalide si sa date est STRICTEMENT INFÉRIEURE à la date de marée.
    # Indice : sale_dates < log_dates
    # -------------------------------------------------------------------------
    invalid_mask = None  # Remplace par ton code (ex: sale_dates < log_dates)

    if invalid_mask is None:
        return {
            "rule_name": "TEMPORAL_CHRONOLOGY_LOGBOOK_VS_SALES",
            "score": 0.0,
            "total_evaluated": len(merged),
            "invalid_count": 0,
            "invalid_sales_ids": []
        }

    invalid_sales_ids = merged.loc[invalid_mask, "sale_id"].tolist()
    invalid_count = len(invalid_sales_ids)
    total_evaluated = len(merged)

    score = ((total_evaluated - invalid_count) / total_evaluated) * 100.0
    score = round(score, 2)

    return {
        "rule_name": "TEMPORAL_CHRONOLOGY_LOGBOOK_VS_SALES",
        "score": score,
        "total_evaluated": total_evaluated,
        "invalid_count": invalid_count,
        "invalid_sales_ids": invalid_sales_ids
    }


def check_catch_vs_sales_volume_consistency(
    logbook_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    max_discrepancy_ratio: float = 2.0
) -> Dict[str, Any]:
    """
    Vérifie la cohérence du tonnage entre les déclarations du Logbook et les ventes réelles.
    """
    required_log = {"trip_id", "species_code", "weight_kg"}
    required_sales = {"trip_id", "species_code", "quantity_kg", "sale_id"}

    if not required_log.issubset(logbook_df.columns) or not required_sales.issubset(sales_df.columns):
        return {
            "rule_name": "VOLUME_CONSISTENCY_LOGBOOK_VS_SALES",
            "score": 100.0,
            "total_evaluated": 0,
            "invalid_count": 0,
            "suspected_fraud_sales_ids": []
        }

    sales_agg = sales_df.groupby(["trip_id", "species_code"]).agg(
        total_sold_kg=("quantity_kg", "sum"),
        sale_ids=("sale_id", list)
    ).reset_index()

    log_subset = logbook_df[["trip_id", "species_code", "weight_kg"]].drop_duplicates(
        subset=["trip_id", "species_code"]
    )

    merged = pd.merge(sales_agg, log_subset, on=["trip_id", "species_code"], how="inner")

    if merged.empty:
        return {
            "rule_name": "VOLUME_CONSISTENCY_LOGBOOK_VS_SALES",
            "score": 100.0,
            "total_evaluated": 0,
            "invalid_count": 0,
            "suspected_fraud_sales_ids": []
        }

    declared_weight = merged["weight_kg"].abs().replace(0, 0.001)

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 2/2 :
    # 1. Calcule le ratio de divergence : ratio = total_sold_kg / declared_weight
    # 2. Définis le masque 'fraud_mask' pour identifier les marées où le ratio
    #    dépasse le seuil toléré (max_discrepancy_ratio).
    # -------------------------------------------------------------------------
    ratio = None       # Remplace par merged["total_sold_kg"] / declared_weight
    fraud_mask = None  # Remplace par ratio > max_discrepancy_ratio

    if fraud_mask is None:
        return {
            "rule_name": "VOLUME_CONSISTENCY_LOGBOOK_VS_SALES",
            "score": 0.0,
            "total_evaluated": len(merged),
            "invalid_count": 0,
            "suspected_fraud_sales_ids": []
        }

    suspected_rows = merged[fraud_mask]
    suspected_sales_ids = [sid for ids in suspected_rows["sale_ids"] for sid in ids]
    invalid_count = len(suspected_rows)
    total_evaluated = len(merged)

    score = ((total_evaluated - invalid_count) / total_evaluated) * 100.0
    score = round(score, 2)

    return {
        "rule_name": "VOLUME_CONSISTENCY_LOGBOOK_VS_SALES",
        "score": score,
        "total_evaluated": total_evaluated,
        "invalid_count": invalid_count,
        "suspected_fraud_sales_ids": suspected_sales_ids
    }


def evaluate_cross_source_consistency(
    logbook_df: pd.DataFrame,
    sales_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Évalue la cohérence globale inter-sources entre LOGBOOK et SALES.
    """
    chrono_res = check_sales_vs_logbook_chronology(logbook_df, sales_df)
    volume_res = check_catch_vs_sales_volume_consistency(logbook_df, sales_df)

    rules = [chrono_res, volume_res]
    all_invalid_ids = set(chrono_res["invalid_sales_ids"] + volume_res["suspected_fraud_sales_ids"])

    avg_score = sum(r["score"] for r in rules) / len(rules)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "rules": rules,
        "total_anomalies": len(all_invalid_ids),
        "anomalous_sales_ids": sorted(list(all_invalid_ids))
    }


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Dimension Cohérence (Branche dev-chaimae)")
    print("=" * 65)

    df_test_log = pd.DataFrame({
        "trip_id": ["TRIP-01", "TRIP-02"],
        "species_code": ["PIL", "OCC"],
        "weight_kg": [1000.0, 500.0],
        "log_date": ["2026-10-01", "2026-10-05"]
    })

    df_test_sales = pd.DataFrame({
        "sale_id": ["S-01", "S-02"],
        "trip_id": ["TRIP-01", "TRIP-02"],
        "species_code": ["PIL", "OCC"],
        "quantity_kg": [1050.0, 3500.0],        # TRIP-02 : 3500kg vs 500kg = ratio 7x (> 2x) = FRAUDE
        "sale_date": ["2026-10-02", "2026-10-01"] # TRIP-02 : vente le 1er oct < marée le 5 oct = ANOMALIE
    })

    res_chrono = check_sales_vs_logbook_chronology(df_test_log, df_test_sales)
    res_vol = check_catch_vs_sales_volume_consistency(df_test_log, df_test_sales)

    print(f"Test Chronologie (Vente >= Marée) : {res_chrono['score']}% (Attendu : 50.0%)")
    print(f"Test Volume (Ratio <= 2.0x)       : {res_vol['score']}% (Attendu : 50.0%)")

    if res_chrono['score'] == 50.0 and res_vol['score'] == 50.0:
        print("\n🎉 BRAVO CHAIMAE ! Tu as validé la dimension Cohérence avec succès !")
        print("👉 Enregistre ton travail avec Git :")
        print("   git add .")
        print("   git commit -m \"Validation de la dimension coherence\"")
        print("   git push origin dev-chaimae")
    else:
        print("\n⏳ Le code attend d'être complété dans les TODO 1 et 2 !")
        print("💡 Aide : Si tu as un doute, regarde le code de référence sur la branche main.")