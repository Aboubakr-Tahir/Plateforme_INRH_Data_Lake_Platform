"""
Générateur de données scientifiques synthétiques pour la plateforme INRH Data Lake.
Respecte scrupuleusement le schéma défini dans schema_donnees.md.

Génère en cascade :
1. LOGBOOK : Déclarations de marée (captures, espèces, engins, zones)
2. SALES   : Ventes aux enchères en criée (liées à LOGBOOK par trip_id et species_code)
3. VMS     : Pings satellite des navires (liés à LOGBOOK par vessel_id et dates)
4. ENV     : Relevés océanographiques des bouées (croisement spatio-temporel)

Injecte des anomalies ciblées (déterministes, statistiques IQR/Z-score, et croisées).
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Répertoire de sortie
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "mock_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Graine aléatoire pour la reproductibilité
random.seed(42)
np.random.seed(42)

# --- 1. Référentiels Maritimes Marocains ---
PORTS = ["Agadir", "Dakhla", "Tan-Tan", "Casablanca", "Nador", "Safi"]

VESSELS = [
    f"MAR-{1000 + i}-{port_code}"
    for i, port_code in enumerate(["AG", "DA", "TT", "CS", "NA", "SA"] * 4)
]

SPECIES = {
    "PIL": {"name": "Sardine", "avg_price": 4.5, "std_price": 0.6, "min_kg": 4000, "max_kg": 18000},
    "MAC": {"name": "Maquereau", "avg_price": 6.2, "std_price": 0.8, "min_kg": 2500, "max_kg": 12000},
    "OCC": {"name": "Poulpe", "avg_price": 78.0, "std_price": 8.5, "min_kg": 800, "max_kg": 4000},
    "HKE": {"name": "Merlu", "avg_price": 42.0, "std_price": 5.0, "min_kg": 500, "max_kg": 3000},
    "SOL": {"name": "Sole", "avg_price": 92.0, "std_price": 9.0, "min_kg": 200, "max_kg": 1500},
}

GEAR_TYPES = ["Chalut de fond", "Senne tournante", "Palangre", "Filet maillant"]

BUOYS = [
    {"sensor_id": "BUOY-AGADIR-01", "lat": 30.42, "lon": -9.75},
    {"sensor_id": "BUOY-DAKHLA-02", "lat": 23.68, "lon": -16.05},
    {"sensor_id": "BUOY-TANTAN-03", "lat": 28.48, "lon": -11.40},
    {"sensor_id": "BUOY-CASA-04", "lat": 33.62, "lon": -7.65},
]


def generate_logbook(n_trips: int = 120) -> pd.DataFrame:
    """Génère les déclarations de journal de bord (LOGBOOK)."""
    base_date = datetime(2026, 9, 20)
    records = []

    for i in range(n_trips):
        trip_id = f"TRIP-2026-{1001 + i}"
        vessel_id = random.choice(VESSELS)
        log_date = base_date + timedelta(days=random.randint(0, 10))
        species_code = random.choice(list(SPECIES.keys()))
        sp_info = SPECIES[species_code]

        # Poids normal tiré d'une distribution uniforme
        weight_kg = round(random.uniform(sp_info["min_kg"], sp_info["max_kg"]), 1)
        gear = random.choice(GEAR_TYPES)

        # Coordonnées côtières normales Atlantique Maroc (Lat: 21 à 34, Lon: -17 à -7)
        lat = round(random.uniform(22.0, 33.5), 4)
        lon = round(random.uniform(-16.5, -8.0), 4)

        # Injection d'anomalies contrôlées
        r = random.random()
        if r < 0.03:
            # 1. Anomalie déterministe : Poids négatif
            weight_kg = -abs(weight_kg)
        elif r < 0.06:
            # 2. Anomalie statistique IQR : Poids disproportionné (120 tonnes pour un navire)
            weight_kg = round(weight_kg * 12.0, 1)
        elif r < 0.08:
            # 3. Anomalie géographique : Coordonnées tombant dans les montagnes de l'Atlas
            lat, lon = 31.8500, -6.2000

        records.append({
            "log_id": f"LOG-2026-{5001 + i}",
            "vessel_id": vessel_id,
            "trip_id": trip_id,
            "log_date": log_date.strftime("%Y-%m-%d"),
            "species_code": species_code,
            "weight_kg": weight_kg,
            "gear_type": gear,
            "latitude": lat,
            "longitude": lon,
        })

    df = pd.DataFrame(records)

    # Injection de 2 doublons stricts (Unicité)
    dup = df.iloc[[5, 12]].copy()
    df = pd.concat([df, dup], ignore_index=True)
    return df


def generate_sales(logbook_df: pd.DataFrame) -> pd.DataFrame:
    """Génère les ventes sous criée (SALES) correspondant aux marées du LOGBOOK."""
    records = []
    sale_idx = 1

    for _, row in logbook_df.iterrows():
        # Une marée peut donner 1 ou 2 lots de vente
        n_sales = random.choice([1, 2])
        base_weight = max(100.0, abs(row["weight_kg"]))
        sp_code = row["species_code"]
        sp_info = SPECIES.get(sp_code, SPECIES["PIL"])
        log_date = datetime.strptime(row["log_date"], "%Y-%m-%d")

        for s in range(n_sales):
            # La vente a lieu le jour même ou 1 jour après la marée
            sale_date = log_date + timedelta(days=random.choice([0, 1]))
            port_id = random.choice(PORTS)

            # Poids vendu proche du poids déclaré (réparti si plusieurs ventes)
            share = 1.0 if n_sales == 1 else (0.6 if s == 0 else 0.4)
            quantity_kg = round(base_weight * share * random.uniform(0.96, 1.04), 1)

            # Prix unitaire moyen
            unit_price = max(1.0, np.random.normal(sp_info["avg_price"], sp_info["std_price"]))
            total_price = round(quantity_kg * unit_price, 2)

            # Injection d'anomalies ciblées
            r = random.random()
            if r < 0.03:
                # 1. Anomalie déterministe : Prix total négatif
                total_price = -abs(total_price)
            elif r < 0.06:
                # 2. Anomalie statistique Z-Score : Faute de frappe sur le prix (ex: 50 MAD/kg au lieu de 4.5)
                unit_price_spike = sp_info["avg_price"] * 10.0
                total_price = round(quantity_kg * unit_price_spike, 2)
            elif r < 0.09:
                # 3. Anomalie croisée (Fraude) : Vente 4x supérieure au Logbook
                quantity_kg = round(quantity_kg * 4.5, 1)
                total_price = round(quantity_kg * unit_price, 2)
            elif r < 0.11:
                # 4. Incohérence temporelle : Vente enregistrée avant la marée
                sale_date = log_date - timedelta(days=3)

            records.append({
                "sale_id": f"SALE-2026-{7000 + sale_idx}",
                "vessel_id": row["vessel_id"],
                "trip_id": row["trip_id"],
                "sale_date": sale_date.strftime("%Y-%m-%d"),
                "port_id": port_id,
                "species_code": sp_code,
                "quantity_kg": quantity_kg,
                "total_price": total_price,
            })
            sale_idx += 1

    return pd.DataFrame(records)


def generate_vms(logbook_df: pd.DataFrame, n_pings: int = 1500) -> pd.DataFrame:
    """Génère les signaux GPS satellites (VMS) pour les navires actifs."""
    unique_vessels = logbook_df["vessel_id"].unique().tolist()
    records = []
    base_time = datetime(2026, 9, 20, 0, 0, 0)

    for i in range(n_pings):
        vessel_id = random.choice(unique_vessels)
        ts = base_time + timedelta(minutes=random.randint(0, 14 * 24 * 60))

        # Position maritime normale au large du Maroc
        lat = round(random.uniform(21.5, 34.5), 4)
        lon = round(random.uniform(-17.0, -7.5), 4)

        # Vitesse normale : soit pêche (2-4 nœuds), soit transit (8-12 nœuds)
        if random.random() < 0.65:
            speed = round(np.random.normal(3.2, 0.5), 1)  # Action de pêche
        else:
            speed = round(np.random.normal(9.5, 1.2), 1)  # Transit

        speed = max(0.0, speed)
        course = random.randint(0, 359)

        # Injection d'anomalies ciblées
        r = random.random()
        if r < 0.025:
            # 1. Anomalie déterministe : Vitesse impossible pour chalutier (80 à 130 nœuds)
            speed = round(random.uniform(85.0, 135.0), 1)
        elif r < 0.050:
            # 2. Anomalie géographique : Point GPS sur la terre ferme
            lat = round(random.uniform(31.2, 32.5), 4)
            lon = round(random.uniform(-6.8, -5.5), 4)
        elif r < 0.070:
            # 3. Anomalie de complétude : Coordonnées manquantes (NaN)
            lat = np.nan
            lon = np.nan

        records.append({
            "vms_id": f"VMS-2026-{100000 + i}",
            "vessel_id": vessel_id,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": lat,
            "longitude": lon,
            "speed": speed,
            "course": course,
        })

    df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
    return df


def generate_env(n_samples: int = 400) -> pd.DataFrame:
    """Génère les relevés océanographiques des bouées (ENV)."""
    records = []
    base_time = datetime(2026, 9, 20, 6, 0, 0)

    for i in range(n_samples):
        buoy = random.choice(BUOYS)
        ts = base_time + timedelta(hours=i * 2)

        # Données réelles normales des eaux côtières marocaines
        sst = round(np.random.normal(18.2, 1.3), 2)       # Température normale 16 - 21°C
        salinity = round(np.random.normal(36.1, 0.3), 2)  # Salinité Atlantique ~36 PSU
        chla = round(np.random.exponential(1.8), 2)       # Chlorophylle-a (distribution asymétrique)

        # Injection d'anomalies ciblées
        r = random.random()
        if r < 0.025:
            # 1. Anomalie physique : Température impossible (panne de sonde à 85°C)
            sst = 85.0
        elif r < 0.050:
            # 2. Anomalie statistique Z-Score : Température anormalement froide (11.5°C)
            sst = 11.5
        elif r < 0.075:
            # 3. Complétude : Salinité manquante (NaN)
            salinity = np.nan

        records.append({
            "env_id": f"ENV-2026-{30000 + i}",
            "sensor_id": buoy["sensor_id"],
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": buoy["lat"],
            "longitude": buoy["lon"],
            "sea_surface_temp": sst,
            "salinity": salinity,
            "chlorophyll_a": chla,
        })

    return pd.DataFrame(records)


def main():
    print("🌊 [INRH] Génération des 4 jeux de données synthétiques...")

    # 1. Logbook
    logbook_df = generate_logbook(n_trips=120)
    logbook_path = os.path.join(OUTPUT_DIR, "logbook_batch_01.csv")
    logbook_df.to_csv(logbook_path, index=False)
    print(f"✅ LOGBOOK généré : {len(logbook_df)} lignes -> {logbook_path}")

    # 2. Sales (en cascade depuis Logbook)
    sales_df = generate_sales(logbook_df)
    sales_path = os.path.join(OUTPUT_DIR, "sales_batch_01.csv")
    sales_df.to_csv(sales_path, index=False)
    print(f"✅ SALES   généré : {len(sales_df)} lignes -> {sales_path}")

    # 3. VMS (pour les navires actifs du Logbook)
    vms_df = generate_vms(logbook_df, n_pings=1500)
    vms_path = os.path.join(OUTPUT_DIR, "vms_batch_01.csv")
    vms_df.to_csv(vms_path, index=False)
    print(f"✅ VMS     généré : {len(vms_df)} lignes -> {vms_path}")

    # 4. ENV (relevés océanographiques spatio-temporels)
    env_df = generate_env(n_samples=400)
    env_path = os.path.join(OUTPUT_DIR, "env_batch_01.csv")
    env_df.to_csv(env_path, index=False)
    print(f"✅ ENV     généré : {len(env_df)} lignes -> {env_path}")

    print("\n🎉 Génération terminée avec succès dans generator/mock_data/ !")


if __name__ == "__main__":
    main()