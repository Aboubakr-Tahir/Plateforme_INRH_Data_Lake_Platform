"""
Générateur de données scientifiques synthétiques INRH avec anomalies réalistes.
Sources générées :
1. VMS     : Balises GPS des navires (vitesse, cap, position)
2. LOGBOOK : Journaux de bord (déclarations de marée, captures)
3. SALES   : Ventes aux enchères dans les criées portuaires
4. ENV     : Relevés océanographiques des bouées (température de l'eau, chlorophylle-a)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "mock_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Référentiels maritimes marocains
VESSELS = [f"MAR-{1000 + i}-{port}" for i, port in enumerate(["AG", "DA", "TT", "CS", "NA", "SA"] * 5)]
PORTS = ["Agadir", "Dakhla", "Tan-Tan", "Casablanca", "Nador", "Safi"]
SPECIES = [
    {"code": "PIL", "name": "Sardine", "avg_price": 4.5},
    {"code": "MAC", "name": "Maquereau", "avg_price": 6.0},
    {"code": "OCC", "name": "Poulpe", "avg_price": 80.0},
    {"code": "HKE", "name": "Merlu", "avg_price": 45.0},
    {"code": "SOL", "name": "Sole", "avg_price": 95.0},
]
BUOYS = [
    {"id": "BUOY-AGADIR-01", "lat": 30.45, "lon": -9.70},
    {"id": "BUOY-DAKHLA-02", "lat": 23.70, "lon": -16.00},
    {"id": "BUOY-TANTAN-03", "lat": 28.45, "lon": -11.35},
    {"id": "BUOY-CASA-04", "lat": 33.65, "lon": -7.60},
]


def generate_vms_data(n_rows: int = 500) -> pd.DataFrame:
    """Génère des pings GPS VMS avec anomalies volontaires."""
    base_time = datetime(2026, 10, 1, 6, 0, 0)
    data = []

    for i in range(n_rows):
        vessel = random.choice(VESSELS)
        ts = base_time + timedelta(minutes=15 * (i % 50))
        # Zone côtière marocaine normale (Atlantique : Lat 21 à 35, Lon -18 à -6)
        lat = round(random.uniform(22.0, 34.0), 4)
        lon = round(random.uniform(-16.0, -8.0), 4)
        speed = round(random.uniform(0.5, 12.0), 1)
        course = random.randint(0, 359)

        # Injection d'anomalies (environ 5% des lignes)
        anomaly_type = None
        rand_val = random.random()
        if rand_val < 0.015:
            speed = round(random.uniform(70.0, 150.0), 1)  # Vitesse impossible pour chalutier
            anomaly_type = "SPEED_OUTLIER"
        elif rand_val < 0.030:
            lat = round(random.uniform(31.5, 32.5), 4)  # Coordonnées sur terre (Montagnes de l'Atlas)
            lon = round(random.uniform(-6.5, -5.5), 4)
            anomaly_type = "GEO_ON_LAND"
        elif rand_val < 0.040:
            lat = np.nan  # Valeur manquante (problème de complétude)
            anomaly_type = "MISSING_COORDINATE"

        data.append({
            "vessel_id": vessel,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": lat,
            "longitude": lon,
            "speed_knots": speed,
            "course_degrees": course,
            "_expected_anomaly": anomaly_type or "NORMAL"
        })

    df = pd.DataFrame(data)
    # Ajouter 2 ou 3 doublons exacts
    duplicates = df.sample(3).copy()
    duplicates["_expected_anomaly"] = "DUPLICATE_ROW"
    df = pd.concat([df, duplicates], ignore_index=True)
    return df


def generate_logbook_data(n_trips: int = 150) -> pd.DataFrame:
    """Génère des déclarations de marée (carnets de pêche)."""
    base_date = datetime(2026, 9, 20)
    data = []

    for i in range(n_trips):
        trip_id = f"TRIP-2026-{1000 + i}"
        vessel = random.choice(VESSELS)
        dep = base_date + timedelta(days=random.randint(0, 8))
        duration = random.randint(2, 7)
        ret = dep + timedelta(days=duration)
        sp = random.choice(SPECIES)
        catch_kg = round(random.uniform(500, 15000), 1)
        gear = random.choice(["Chalut", "Palangre", "Senne", "Filet maillant"])

        anomaly_type = None
        rand_val = random.random()
        if rand_val < 0.03:
            ret = dep - timedelta(days=2)  # Date retour < date départ (Incohérence chronologique)
            anomaly_type = "INVALID_CHRONOLOGY"
        elif rand_val < 0.05:
            catch_kg = -abs(catch_kg)  # Poids négatif
            anomaly_type = "NEGATIVE_WEIGHT"
        elif rand_val < 0.07:
            catch_kg = round(random.uniform(500000, 900000), 1)  # Poids aberrant (500 tonnes pour un bateau)
            anomaly_type = "CATCH_WEIGHT_OUTLIER"

        data.append({
            "trip_id": trip_id,
            "vessel_id": vessel,
            "departure_date": dep.strftime("%Y-%m-%d"),
            "return_date": ret.strftime("%Y-%m-%d"),
            "species_code": sp["code"],
            "catch_weight_kg": catch_kg,
            "gear_type": gear,
            "_expected_anomaly": anomaly_type or "NORMAL"
        })

    return pd.DataFrame(data)


def generate_sales_data(logbook_df: pd.DataFrame) -> pd.DataFrame:
    """Génère les ventes réelles à la criée correspondant aux marées."""
    data = []
    for i, row in logbook_df.iterrows():
        if row["_expected_anomaly"] == "INVALID_CHRONOLOGY":
            continue

        sp_code = row["species_code"]
        sp_info = next((s for s in SPECIES if s["code"] == sp_code), SPECIES[0])
        port = random.choice(PORTS)

        # En général, le poids vendu est très proche du poids estimé dans le logbook (+/- 5%)
        base_weight = abs(row["catch_weight_kg"]) if not pd.isna(row["catch_weight_kg"]) else 1000
        weight_sold = round(base_weight * random.uniform(0.95, 1.05), 1)
        price_per_kg = round(sp_info["avg_price"] * random.uniform(0.85, 1.15), 2)

        anomaly_type = None
        rand_val = random.random()
        if rand_val < 0.03:
            price_per_kg = -5.0  # Prix négatif
            anomaly_type = "NEGATIVE_PRICE"
        elif rand_val < 0.06:
            # Fraude / Écart massif : vendu 5 fois plus que déclaré
            weight_sold = base_weight * 5
            anomaly_type = "MISMATCH_LOGBOOK_SALES"

        data.append({
            "sale_id": f"SALE-2026-{5000 + i}",
            "trip_id": row["trip_id"],
            "vessel_id": row["vessel_id"],
            "port_name": port,
            "sale_date": row["return_date"],
            "species_code": sp_code,
            "weight_kg": weight_sold,
            "price_mad_per_kg": price_per_kg,
            "_expected_anomaly": anomaly_type or "NORMAL"
        })

    return pd.DataFrame(data)


def generate_env_data(n_records: int = 300) -> pd.DataFrame:
    """Génère des mesures océanographiques de bouées côtières."""
    base_time = datetime(2026, 10, 1, 0, 0, 0)
    data = []

    for i in range(n_records):
        buoy = random.choice(BUOYS)
        ts = base_time + timedelta(hours=i % 72)
        # Températures réelles côte marocaine (16°C à 22°C)
        temp = round(random.uniform(16.0, 21.5), 2)
        salinity = round(random.uniform(35.5, 36.8), 2)
        chlorophyll = round(random.uniform(0.5, 4.5), 2)

        anomaly_type = None
        rand_val = random.random()
        if rand_val < 0.02:
            temp = 85.0  # Erreur capteur thermique
            anomaly_type = "TEMP_OUTLIER_HIGH"
        elif rand_val < 0.04:
            temp = -15.0  # Erreur capteur thermique
            anomaly_type = "TEMP_OUTLIER_LOW"
        elif rand_val < 0.06:
            salinity = np.nan  # Donnée manquante
            anomaly_type = "MISSING_SALINITY"

        data.append({
            "buoy_id": buoy["id"],
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": buoy["lat"],
            "longitude": buoy["lon"],
            "water_temp_celsius": temp,
            "salinity_psu": salinity,
            "chlorophyll_a": chlorophyll,
            "_expected_anomaly": anomaly_type or "NORMAL"
        })

    return pd.DataFrame(data)


def main():
    print("🌊 Génération des jeux de données INRH en cours...")
    vms_df = generate_vms_data(600)
    logbook_df = generate_logbook_data(180)
    sales_df = generate_sales_data(logbook_df)
    env_df = generate_env_data(350)

    vms_path = os.path.join(OUTPUT_DIR, "vms_batch_01.csv")
    logbook_path = os.path.join(OUTPUT_DIR, "logbook_batch_01.csv")
    sales_path = os.path.join(OUTPUT_DIR, "sales_batch_01.csv")
    env_path = os.path.join(OUTPUT_DIR, "env_batch_01.csv")

    vms_df.to_csv(vms_path, index=False)
    logbook_df.to_csv(logbook_path, index=False)
    sales_df.to_csv(sales_path, index=False)
    env_df.to_csv(env_path, index=False)

    print(f"✅ VMS généré     : {len(vms_df)} lignes -> {vms_path}")
    print(f"✅ LOGBOOK généré : {len(logbook_df)} lignes -> {logbook_path}")
    print(f"✅ SALES généré   : {len(sales_df)} lignes -> {sales_path}")
    print(f"✅ ENV généré     : {len(env_df)} lignes -> {env_path}")
    print("\n✨ Tous les fichiers ont été générés avec succès dans generator/mock_data/ !")


if __name__ == "__main__":
    main()
