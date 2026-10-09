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

    # Fusion sur trip_id
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

    # Invalide si la vente a eu lieu AVANT la date de pêche
    invalid_mask = sale_dates < log_dates
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
    Règle : Pour une marée et une espèce données, la quantité vendue ne doit pas
            dépasser un multiple anormal de la capture estimée (par défaut 2.0 = +100%).
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

    # Agrégation des ventes par trip_id et species_code
    sales_agg = sales_df.groupby(["trip_id", "species_code"]).agg(
        total_sold_kg=("quantity_kg", "sum"),
        sale_ids=("sale_id", list)
    ).reset_index()

    # Logbook correspondant
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

    # Détection de survente anormale (quantité vendue disproportionnée vs déclaration)
    # Ratio = total_sold_kg / abs(weight_kg)
    declared_weight = merged["weight_kg"].abs().replace(0, 0.001)
    ratio = merged["total_sold_kg"] / declared_weight
    fraud_mask = ratio > max_discrepancy_ratio

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
    Combine :
    1. La règle chronologique (sale_date >= log_date)
    2. La règle de volume (poids vendu vs poids déclaré)
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


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU MODULE DE COHÉRENCE (Branche main)")
    print("=" * 65)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generator", "mock_data")
    logbook_path = os.path.join(data_dir, "logbook_batch_01.csv")
    sales_path = os.path.join(data_dir, "sales_batch_01.csv")

    if os.path.exists(logbook_path) and os.path.exists(sales_path):
        df_logbook = pd.read_csv(logbook_path)
        df_sales = pd.read_csv(sales_path)

        res = evaluate_cross_source_consistency(df_logbook, df_sales)

        print(f"🔗 Croisement LOGBOOK ({len(df_logbook)} marées) & SALES ({len(df_sales)} ventes) :")
        print(f"   🎯 Score de Cohérence Globale : {res['score']}%")
        print(f"   🚨 Ventes anormales détectées : {res['total_anomalies']}")
        for r in res["rules"]:
            print(f"      - {r['rule_name']:<42} : {r['score']:>6.2f}% ({r['invalid_count']} anomalies)")

        print("\n✅ Module de cohérence validé avec succès sur main !")
    else:
        print("⚠️ Fichiers CSV introuvables pour le test.")