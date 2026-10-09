"""
Module de Calcul du Score de Qualité Global (Quality Scoring)
Calcule la note finale selon la formule pondérée des 4 dimensions DAMA :

Formule Mathématique :
Score Global = (w_comp * Completude) + (w_val * Validite) + (w_uniq * Unicite) + (w_cons * Coherence)
avec sum(w_i) = 1.0

Pondération standard pour le projet INRH :
- Complétude (w_comp = 0.25) : 25%
- Validité   (w_val  = 0.35) : 35%
- Unicité    (w_uniq = 0.20) : 20%
- Cohérence  (w_cons = 0.20) : 20%

🎯 EXERCICE APPLICATIF (Chaimae) :
Complète les sections marquées par # TODO (Chaimae).
Pour tester ton travail, exécute simplement ce fichier dans ton terminal :
    python quality_engine/scoring.py
"""

from typing import Dict, Any


DEFAULT_WEIGHTS = {
    "completeness": 0.25,
    "validity": 0.35,
    "uniqueness": 0.20,
    "consistency": 0.20
}


def compute_global_score(
    completeness_score: float,
    validity_score: float,
    uniqueness_score: float,
    consistency_score: float,
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Calcule le score de qualité global pondéré (entre 0.0% et 100.0%)
    et attribue le statut et le grade académique correspondant.
    """
    w = weights if weights else DEFAULT_WEIGHTS

    total_weights = sum(w.values())
    w_norm = {k: v / total_weights for k, v in w.items()}

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 1/2 :
    # Calcule le 'global_score' en appliquant la somme pondérée :
    # global_score = (completeness_score * w_norm["completeness"]) + ...
    # -------------------------------------------------------------------------
    global_score = None  # Remplace par ta formule pondérée

    if global_score is None:
        return {
            "global_score": 0.0,
            "grade": "Non calculé",
            "status": "PENDING",
            "dimensions": {},
            "applied_weights": w_norm
        }

    global_score = round(float(global_score), 2)

    # -------------------------------------------------------------------------
    # TODO (Chaimae) 2/2 :
    # Attribue le grade et le statut selon les règles métier :
    # - Si global_score >= 90.0 : grade = "A (Excellent)", status = "PASSED"
    # - Si global_score >= 75.0 : grade = "B (Bon)",       status = "PASSED"
    # - Si global_score >= 60.0 : grade = "C (Moyen)",     status = "WARNING"
    # - Sinon                   : grade = "D (Critique)",  status = "REJECTED"
    # -------------------------------------------------------------------------
    grade = "Non défini"
    status = "NON_VALIDE"

    # Remplace par ton bloc if/elif/else :
    if global_score >= 90.0:
        grade = "A (Excellent)"
        status = "PASSED"
    elif global_score >= 75.0:
        grade = "B (Bon)"
        status = "PASSED"
    elif global_score >= 60.0:
        grade = "C (Moyen)"
        status = "WARNING"
    else:
        grade = "D (Critique)"
        status = "REJECTED"

    return {
        "global_score": global_score,
        "grade": grade,
        "status": status,
        "dimensions": {
            "completeness": round(float(completeness_score), 2),
            "validity": round(float(validity_score), 2),
            "uniqueness": round(float(uniqueness_score), 2),
            "consistency": round(float(consistency_score), 2)
        },
        "applied_weights": w_norm
    }


# =============================================================================
# 🧪 BLOC DE VALIDATION AUTOMATIQUE (Exécute ce fichier pour tester)
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("👩‍💻 TEST DE TON CODE : Scoring Global (Branche dev-chaimae)")
    print("=" * 65)

    # Test avec 4 scores d'exemple : 100, 80, 90, 70
    # Score attendu : (100*0.25) + (80*0.35) + (90*0.20) + (70*0.20) = 25 + 28 + 18 + 14 = 85.0%
    res = compute_global_score(
        completeness_score=100.0,
        validity_score=80.0,
        uniqueness_score=90.0,
        consistency_score=70.0
    )

    print(f"Score Global calculé : {res['global_score']}% (Attendu : 85.0%)")
    print(f"Grade attribué       : {res['grade']} (Attendu : B (Bon))")
    print(f"Statut               : {res['status']} (Attendu : PASSED)")

    if res['global_score'] == 85.0 and res['grade'] == "B (Bon)" and res['status'] == "PASSED":
        print("\n🎉 BRAVO CHAIMAE ! Tu as validé le Scoring Global avec succès !")
        print("👉 Enregistre ton travail avec Git :")
        print("   git add .")
        print("   git commit -m \"Validation du scoring global de qualite\"")
        print("   git push origin dev-chaimae")
    else:
        print("\n⏳ Le code attend d'être complété dans le TODO 1 !")
        print("💡 Aide : Si tu as un doute, regarde le code de référence sur la branche main.")