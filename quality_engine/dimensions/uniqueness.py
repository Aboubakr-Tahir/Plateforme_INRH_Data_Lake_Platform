"""
Dimension 3 : Unicité (Uniqueness)
Mesure l'absence de doublons dans le jeu de données.
Deux niveaux :
1. Doublons stricts : lignes entièrement identiques
2. Doublons de clé : plusieurs lignes avec le même identifiant métier (ex: même ping VMS pour un même navire à la même seconde)
"""

from typing import Dict, Any, List
import pandas as pd


def check_uniqueness(df: pd.DataFrame, key_columns: List[str] = None) -> Dict[str, Any]:
    """
    Évalue le taux d'unicité d'un DataFrame.
    Si key_columns est fourni, vérifie l'unicité sur ces colonnes spécifiques (ex: ['vessel_id', 'timestamp']).
    Sinon, vérifie les doublons complets.
    """
    if df.empty:
        return {"score": 100.0, "duplicate_count": 0, "duplicate_indices": []}

    subset = [c for c in key_columns if c in df.columns] if key_columns else None
    duplicate_mask = df.duplicated(subset=subset, keep="first")
    duplicate_indices = df[duplicate_mask].index.tolist()
    duplicate_count = len(duplicate_indices)

    # Score : 100% si aucun doublon, 0% si toutes les lignes sont des doublons
    score = round(((len(df) - duplicate_count) / len(df)) * 100.0, 2)

    return {
        "score": score,
        "duplicate_count": duplicate_count,
        "duplicate_indices": duplicate_indices
    }
