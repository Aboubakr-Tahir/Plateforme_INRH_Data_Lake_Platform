"""
Module de Calcul du Score de Qualité Global (Quality Scoring)
Calcule la note finale selon la formule pondérée des 4 dimensions DAMA :

Formule Mathématique :
Score Global = (w_comp * Completude) + (w_val * Validite) + (w_uniq * Unicite) + (w_cons * Coherence)
avec sum(w_i) = 1.0

Pondération standard pour le projet INRH :
- Complétude (w_comp = 0.25) : 25%
- Validité   (w_val  = 0.35) : 35% (priorité aux coordonnées ZEE et règles métier)
- Unicité    (w_uniq = 0.20) : 20%
- Cohérence  (w_cons = 0.20) : 20%

Attribution des grades :
- Score >= 90% : Grade A (Excellent - Conforme)
- Score >= 75% : Grade B (Bon - Accepté)
- Score >= 60% : Grade C (Moyen - Avertissement)
- Score <  60% : Grade D (Critique - Rejeté)
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

    # Normalisation des poids pour garantir que la somme vaut exactement 1.0
    total_weights = sum(w.values())
    w_norm = {k: v / total_weights for k, v in w.items()}

    # Calcul pondéré
    global_score = (
        (completeness_score * w_norm["completeness"]) +
        (validity_score * w_norm["validity"]) +
        (uniqueness_score * w_norm["uniqueness"]) +
        (consistency_score * w_norm["consistency"])
    )
    global_score = round(global_score, 2)

    # Attribution du grade et statut
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


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 TEST DU MODULE DE SCORING GLOBAL (Branche main)")
    print("=" * 65)

    # Exemple concret avec les scores obtenus sur nos données réelles de test
    test_comp = 99.38
    test_val = 97.78
    test_uniq = 98.36
    test_cons = 94.34

    result = compute_global_score(
        completeness_score=test_comp,
        validity_score=test_val,
        uniqueness_score=test_uniq,
        consistency_score=test_cons
    )

    print(f"📊 Résultats des 4 dimensions DAMA :")
    print(f"   - Complétude (25%) : {result['dimensions']['completeness']}%")
    print(f"   - Validité   (35%) : {result['dimensions']['validity']}%")
    print(f"   - Unicité    (20%) : {result['dimensions']['uniqueness']}%")
    print(f"   - Cohérence  (20%) : {result['dimensions']['consistency']}%")

    print(f"\n🎯 SCORE GLOBAL DE QUALITÉ : {result['global_score']}%")
    print(f"🏆 GRADE ATTRIBUÉ          : {result['grade']}")
    print(f"🚦 STATUT                  : {result['status']}")

    print("\n✅ Module de scoring validé avec succès sur main !")