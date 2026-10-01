"""
Fichier de brouillon rapide pour tester des filtres et règles qualité.
Chaimae peut exécuter ce fichier directement avec :
python notebooks/scratch_test.py
"""

import os
import sys
import pandas as pd

# Permet d'importer directement depuis quality_engine
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from generator.generate_all import generate_vms_data
from quality_engine.dimensions.completeness import evaluate_dataset_completeness
from quality_engine.dimensions.validity import check_range_validity, check_maritime_coordinates
from quality_engine.scoring import compute_global_score

print("=" * 60)
print("🐟 TEST BROUILLON : Analyse d'un échantillon VMS")
print("=" * 60)

# 1. Générer 100 lignes de test
df = generate_vms_data(100)
print(f"Dataset généré : {len(df)} lignes.")
print("\nAperçu des 5 premières lignes :")
print(df[["vessel_id", "timestamp", "latitude", "longitude", "speed_knots"]].head())

# 2. Test de la complétude
comp = evaluate_dataset_completeness(df, mandatory_columns=["vessel_id", "latitude", "longitude", "speed_knots"])
print(f"\n1. Complétude : {comp['score']}% (Valeurs manquantes: {comp['missing_count']})")

# 3. Test de la validité géographique
geo = check_maritime_coordinates(df)
print(f"2. Validité Géographique (eaux marocaines) : {geo['score']}% ({geo['invalid_count']} points hors zone)")

# 4. Test de la vitesse
speed = check_range_validity(df, "speed_knots", 0.0, 35.0)
print(f"3. Validité Vitesse (0 - 35 nœuds) : {speed['score']}% ({speed['invalid_count']} vitesses anormales)")

# 5. Score Global
global_res = compute_global_score(
    completeness_score=comp["score"],
    validity_score=round((geo["score"] + speed["score"]) / 2, 2),
    uniqueness_score=98.0,
    consistency_score=100.0
)

print("\n" + "=" * 60)
print(f"🎯 SCORE GLOBAL DE QUALITÉ : {global_res['global_score']}%")
print(f"🏆 NIVEAU OBTENU : {global_res['grade']}")
print("=" * 60)
