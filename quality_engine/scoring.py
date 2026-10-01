"""
Module de Calcul du Score de Qualité Global (Quality Scoring)
Calcule le score global selon la formule pondérée des 4 dimensions DAMA :
Score Global = (w_c * Completude) + (w_v * Validite) + (w_u * Unicite) + (w_co * Coherence)
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
    Calcule le score global pondéré (0% - 100%) et attribue une lettre de grade qualité (A, B, C, D, E).
    """
    w = weights if weights else DEFAULT_WEIGHTS

    # Normalisation de la somme des poids
    total_w = sum(w.values())
    w_norm = {k: v / total_w for k, v in w.items()}

    global_score = (
        (completeness_score * w_norm["completeness"]) +
        (validity_score * w_norm["validity"]) +
        (uniqueness_score * w_norm["uniqueness"]) +
        (consistency_score * w_norm["consistency"])
    )
    global_score = round(global_score, 2)

    # Attribution du niveau de qualité
    if global_score >= 90.0:
        grade = "A (Excellent)"
        status = "PASSED"
    elif global_score >= 75.0:
        grade = "B (Bon)"
        status = "PASSED"
    elif global_score >= 60.0:
        grade = "C (Moyen - Avertissements)"
        status = "WARNING"
    elif global_score >= 40.0:
        grade = "D (Médiocre)"
        status = "FAILED"
    else:
        grade = "E (Critique - Rejeté)"
        status = "REJECTED"

    return {
        "global_score": global_score,
        "grade": grade,
        "status": status,
        "sub_scores": {
            "completeness": completeness_score,
            "validity": validity_score,
            "uniqueness": uniqueness_score,
            "consistency": consistency_score
        },
        "applied_weights": w_norm
    }
