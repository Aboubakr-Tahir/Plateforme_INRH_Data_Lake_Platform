"""
Dimension 1 : Complétude (Completeness)
Mesure le taux de présence des valeurs requises (absence de valeurs nulles ou manquantes).

Norme DAMA International :
Formule colonne  : (Nombre de valeurs non-nulles) / (Nombre total de lignes) * 100
Formule globale  : Moyenne des scores de complétude des colonnes obligatoires

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/dimensions/completeness.py
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

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # 1. Compte le nombre de valeurs non-nulles (non-NaN) dans df[column].
    #    Indice : utilise la fonction .notna().sum() de Pandas.
    # 2. Calcule le score en pourcentage : (non-nulles / total) * 100.
    # -------------------------------------------------------------------------
    non_null_count = None  # Remplace None par ton code (ex: df[column].notna().sum())
    score = None           # Remplace None par la formule de pourcentage

    # Sécurité pendant que tu complètes
    if non_null_count is None or score is None:
        return 0.0

    return round(float(score), 2)


def evaluate_dataset_completeness(
    df: pd.DataFrame,
    mandatory_columns: List[str] = None
) -> Dict[str, Any]:
    """
    Évalue la complétude globale d'un DataFrame sur un ensemble de colonnes obligatoires.
    """
    if df.empty:
        return {
            "score": 0.0,
            "details": {},
            "missing_count": 0,
            "missing_indices": []
        }

    cols_to_check = mandatory_columns if mandatory_columns else list(df.columns)
    
    details = {}
    total_missing = 0
    missing_indices_set = set()

    for col in cols_to_check:
        if col in df.columns:
            # Appel de la fonction que tu as complétée plus haut
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
            details[col] = {
                "completeness_pct": 0.0,
                "missing_count": len(df)
            }
            total_missing += len(df)
            missing_indices_set.update(df.index.tolist())

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 3/3 :
    # Calcule la moyenne des scores de complétude de toutes les colonnes testées.
    # Indice : la liste des scores est [d["completeness_pct"] for d in details.values()]
    # avg_score = somme des scores / nombre de colonnes
    # -------------------------------------------------------------------------
    avg_score = 0.0  # Remplace par ta formule de calcul de la moyenne

    return {
        "score": round(float(avg_score), 2),
        "details": details,
        "missing_count": total_missing,
        "missing_indices": sorted(list(missing_indices_set))
    }


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Dimension Complétude (Branche dev-chaimae)")
    print("=" * 65)

    # Petit jeu de test simple
    df_test = pd.DataFrame({
        "vessel_id": ["MAR-01", "MAR-02", None, "MAR-04"],  # 3 non-nulles sur 4 = 75%
        "speed": [10.5, 12.0, 8.5, 0.0]                     # 4 non-nulles sur 4 = 100%
    })

    score_vessel = check_column_completeness(df_test, "vessel_id")
    score_speed = check_column_completeness(df_test, "speed")

    print(f"Test colonne 'vessel_id' : {score_vessel}% (Attendu : 75.0%)")
    print(f"Test colonne 'speed'     : {score_speed}% (Attendu : 100.0%)")

    if score_vessel == 75.0 and score_speed == 100.0:
        res = evaluate_dataset_completeness(df_test)
        print(f"Score Global du test     : {res['score']}% (Attendu : 87.5%)")
        if res['score'] == 87.5:
            print("\n🎉 BRAVO CHAIMAE ! Tu as validé la dimension Complétude avec succès !")
            print("👉 Tu peux maintenant enregistrer ton travail avec Git :")
            print("   git add .")
            print("   git commit -m \"Validation de la dimension complétude\"")
            print("   git push origin dev-chaimae")
        else:
            print("\n⚠️ Presque ! Vérifie ton calcul de moyenne (TODO 3).")
    else:
        print("\n⏳ Le code attend d'être complété dans les TODO 1 et 2 !")
        print("💡 Aide : Si tu as un doute, regarde le code de référence sur la branche main.")