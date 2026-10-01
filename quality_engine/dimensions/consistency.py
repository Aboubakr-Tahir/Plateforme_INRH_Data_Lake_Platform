"""
Dimension 4 : Cohérence (Consistency)
Vérifie la logique relationnelle et temporelle entre plusieurs colonnes ou plusieurs tables.
Exemples INRH :
- Chronologie : Date de retour de marée >= Date de départ
- Cohérence croisée : Les captures déclarées dans le Logbook doivent être cohérentes avec les ventes à la criée
"""

from typing import Dict, Any
import pandas as pd


def check_date_chronology(df: pd.DataFrame, start_col: str, end_col: str) -> Dict[str, Any]:
    """Vérifie que la date de fin est postérieure ou égale à la date de début."""
    if start_col not in df.columns or end_col not in df.columns or df.empty:
        return {"score": 100.0, "invalid_count": 0, "invalid_indices": []}

    start_dates = pd.to_datetime(df[start_col], errors="coerce")
    end_dates = pd.to_datetime(df[end_col], errors="coerce")

    # Invalide si la date de fin est STRICTEMENT inférieure à la date de début
    invalid_mask = (end_dates < start_dates) & start_dates.notna() & end_dates.notna()
    invalid_indices = df[invalid_mask].index.tolist()
    invalid_count = len(invalid_indices)

    evaluated_count = (start_dates.notna() & end_dates.notna()).sum()
    score = round(((evaluated_count - invalid_count) / evaluated_count * 100.0), 2) if evaluated_count > 0 else 100.0

    return {
        "score": score,
        "invalid_count": invalid_count,
        "invalid_indices": invalid_indices
    }


def check_logbook_vs_sales_consistency(logbook_df: pd.DataFrame, sales_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Vérifie la cohérence croisée entre le carnet de pêche (Logbook) et la vente en criée (Sales).
    Règle : Le poids vendu ne doit pas dépasser plus de 150% du poids déclaré dans le carnet de pêche.
    """
    if "trip_id" not in logbook_df.columns or "trip_id" not in sales_df.columns:
        return {"score": 100.0, "mismatch_count": 0}

    merged = pd.merge(sales_df, logbook_df, on="trip_id", suffixes=("_sales", "_logbook"))
    if merged.empty:
        return {"score": 100.0, "mismatch_count": 0}

    # Ratio de divergence
    mismatch_mask = merged["weight_kg"] > (merged["catch_weight_kg"] * 1.5)
    mismatch_count = int(mismatch_mask.sum())
    total_compared = len(merged)

    score = round(((total_compared - mismatch_count) / total_compared * 100.0), 2) if total_compared > 0 else 100.0

    return {
        "score": score,
        "mismatch_count": mismatch_count,
        "total_compared": total_compared
    }
