"""
Dimension 1 : Complétude (Completeness)
Mesure le taux de présence des valeurs requises (absence de valeurs nulles ou manquantes).
Formule : Complétude = (Nombre de valeurs non nulles) / (Nombre total de valeurs attendues) * 100
"""

from typing import List, Dict, Any
import pandas as pd


def check_column_completeness(df: pd.DataFrame, column: str) -> float:
    """Calcule le taux de complétude d'une colonne donnée (entre 0% et 100%)."""
    if column not in df.columns or len(df) == 0:
        return 0.0
    non_null_count = df[column].notna().sum()
    return round((non_null_count / len(df)) * 100.0, 2)


def evaluate_dataset_completeness(df: pd.DataFrame, mandatory_columns: List[str] = None) -> Dict[str, Any]:
    """
    Évalue la complétude globale d'un dataset sur ses colonnes obligatoires.
    Retourne :
      - 'score': score moyen de complétude (0-100)
      - 'details': détails par colonne
      - 'missing_count': nombre total de valeurs manquantes
    """
    if df.empty:
        return {"score": 0.0, "details": {}, "missing_count": 0}

    columns_to_check = mandatory_columns if mandatory_columns else [c for c in df.columns if not c.startswith("_")]
    details = {}
    total_missing = 0

    for col in columns_to_check:
        if col in df.columns:
            score_col = check_column_completeness(df, col)
            missing = int(df[col].isna().sum())
            total_missing += missing
            details[col] = {"completeness_pct": score_col, "missing_rows": missing}
        else:
            details[col] = {"completeness_pct": 0.0, "missing_rows": len(df)}
            total_missing += len(df)

    avg_score = round(sum(d["completeness_pct"] for d in details.values()) / len(details), 2)

    return {
        "score": avg_score,
        "details": details,
        "missing_count": total_missing
    }
