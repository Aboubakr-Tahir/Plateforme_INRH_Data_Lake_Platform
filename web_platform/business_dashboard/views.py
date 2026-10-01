import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings


def business_home(request):
    """
    Dashboard Scientifique & Métier INRH :
    Consomme les agrégations de la couche Gold (ou mock data si MinIO n'est pas encore peuplé).
    """
    mock_data_dir = os.path.join(settings.BASE_DIR.parent, "generator", "mock_data")
    sales_file = os.path.join(mock_data_dir, "sales_batch_01.csv")
    vms_file = os.path.join(mock_data_dir, "vms_batch_01.csv")

    species_stats = []
    port_stats = []
    total_sales_weight = 0
    total_revenue_mad = 0

    if os.path.exists(sales_file):
        try:
            df_sales = pd.read_csv(sales_file)
            # Ne garder que les données valides
            df_clean = df_sales[df_sales["price_mad_per_kg"] > 0].copy()
            df_clean["revenue"] = df_clean["weight_kg"] * df_clean["price_mad_per_kg"]

            total_sales_weight = round(df_clean["weight_kg"].sum() / 1000.0, 1)  # en Tonnes
            total_revenue_mad = round(df_clean["revenue"].sum(), 2)

            # Agréger par espèce (Gold layer simulation)
            sp_agg = df_clean.groupby("species_code").agg(
                total_weight=("weight_kg", "sum"),
                avg_price=("price_mad_per_kg", "mean"),
                sales_count=("sale_id", "count")
            ).reset_index()

            species_names = {"PIL": "Sardine", "MAC": "Maquereau", "OCC": "Poulpe", "HKE": "Merlu", "SOL": "Sole"}
            sp_agg["name"] = sp_agg["species_code"].map(species_names).fillna(sp_agg["species_code"])
            species_stats = sp_agg.to_dict(orient="records")

            # Agréger par port
            port_agg = df_clean.groupby("port_name").agg(
                port_weight=("weight_kg", "sum"),
                port_revenue=("revenue", "sum")
            ).reset_index()
            port_stats = port_agg.to_dict(orient="records")
        except Exception as e:
            print(f"Erreur chargement Sales: {e}")

    active_vessels_count = 0
    if os.path.exists(vms_file):
        try:
            df_vms = pd.read_csv(vms_file)
            active_vessels_count = df_vms["vessel_id"].nunique()
        except Exception:
            pass

    context = {
        "species_stats": species_stats,
        "port_stats": port_stats,
        "total_sales_weight_tons": total_sales_weight,
        "total_revenue_mad": total_revenue_mad,
        "active_vessels_count": active_vessels_count,
    }
    return render(request, "business_dashboard/home.html", context)
