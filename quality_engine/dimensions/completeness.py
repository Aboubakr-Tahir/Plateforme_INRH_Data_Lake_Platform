"""
Dimension 1 : Complétude (Completeness)
Mesure le taux de présence des valeurs requises (absence de valeurs nulles ou manquantes).

Norme DAMA International :
Formule colonne  : (Nombre de valeurs non-nulles) / (Nombre total de lignes) * 100
Formule globale  : Moyenne des scores de complétude des colonnes obligatoires
"""

import os
from typing import List, Dict, Any
import pandas as pd


def check_column_completeness(df: pd.DataFrame, column: str) -> float:
    """
    Calcule le taux de complétude d'une colonne donnée (entre 0.0% et 100.0%).
    """
    if column not in df.columns or len(df) == 0:
        return 0.0

    total_rows = len(df)
    # Compte le nombre de valeurs non-nulles (non-NaN)
    non_null_count = int(df[column].notna().sum())

    # Calcul du ratio en pourcentage
    score = (non_null_count / total_rows) * 100.0
    return round(score, 2)


def evaluate_dataset_completeness(
    df: pd.DataFrame,
    mandatory_columns: List[str] = None
) -> Dict[str, Any]:
    """
    Évalue la complétude globale d'un DataFrame sur un ensemble de colonnes obligatoires.
    
    Retourne un dictionnaire contenant :
      - 'score': score moyen de complétude (0-100%)
      - 'details': taux et nombre de valeurs manquantes par colonne
      - 'missing_count': nombre total de valeurs manquantes
      - 'missing_indices': indices des lignes contenant au moins une valeur manquante
    """
    if df.empty:
        return {
            "score": 0.0,
            "details": {},
            "missing_count": 0,
            "missing_indices": []
        }

    # Si aucune colonne n'est spécifiée, on évalue toutes les colonnes réelles
    cols_to_check = mandatory_columns if mandatory_columns else list(df.columns)
    
    details = {}
    total_missing = 0
    missing_indices_set = set()

    for col in cols_to_check:
        if col in df.columns:
            comp_pct = check_column_completeness(df, col)
            missing_rows = int(df[col].isna().sum())
            total_missing += missing_rows

            if missing_rows > 0:
                missing_indices_set.update(df[df[col].isna()].index.tolist())

            details[col] = {
                "completeness_pct": comp_pct,
                "missing_count": missing_rows
            }
        else:
            # Colonne obligatoire absente du dataset = 0% de complétude
            details[col] = {
                "completeness_pct": 0.0,
                "missing_count": len(df)
            }
            total_missing += len(df)
            missing_indices_set.update(df.index.tolist())

    # Score global = moyenne des complétudes des colonnes vérifiées
    avg_score = sum(d["completeness_pct"] for d in details.values()) / len(details)
    avg_score = round(avg_score, 2)

    return {
        "score": avg_score,
        "details": details,
        "missing_count": total_missing,
        "missing_indices": sorted(list(missing_indices_set))
    }


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU MODULE DE COMPLÉTUDE (Branche main)")
    print("=" * 65)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generator", "mock_data")
    vms_path = os.path.join(data_dir, "vms_batch_01.csv")

    if not os.path.exists(vms_path):
        print(f"⚠️ Fichier de test introuvable : {vms_path}")
    else:
        df_vms = pd.read_csv(vms_path)
        print(f"📄 Données chargées : {len(df_vms)} lignes.")

        # Test sur les colonnes clés
        mandatory = ["vms_id", "vessel_id", "timestamp", "latitude", "longitude", "speed"]
        res = evaluate_dataset_completeness(df_vms, mandatory_columns=mandatory)

        print(f"\n🎯 Score Global de Complétude : {res['score']}%")
        print(f"❌ Valeurs manquantes totales : {res['missing_count']}")
        print(f"🔍 Détail par colonne :")
        for c, d in res["details"].items():
            print(f"   - {c:<12} : {d['completeness_pct']:>6.2f}% (manquants: {d['missing_count']})")

        print("\n✅ Module de complétude validé avec succès sur main !")