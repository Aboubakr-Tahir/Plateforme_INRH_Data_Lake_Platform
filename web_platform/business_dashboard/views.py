from django.conf import settings
from django.shortcuts import render

from data_pipeline.minio_client import get_client, read_from_gold


def _read_gold(object_name):
    try:
        return read_from_gold(object_name, get_client()).to_dict("records")
    except Exception:
        return []


def home(request):
    batch_id = request.GET.get("batch_id", "batch_01")
    prefix = f"{batch_id}/"
    return render(request, "business_dashboard/home.html", {
        "batch_id": batch_id,
        "sales": _read_gold(prefix + "sales_by_port_species.parquet"),
        "catches": _read_gold(prefix + "catches_by_species.parquet"),
        "environment": _read_gold(prefix + "environment_by_sensor.parquet"),
        "quality": _read_gold(prefix + "quality_kpis.parquet"),
    })