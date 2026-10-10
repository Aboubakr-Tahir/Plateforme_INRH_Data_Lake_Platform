"""
Configuration Celery pour l'orchestration asynchrone des pipelines de données.
Utilise Redis comme courtier de messages (Broker).
"""

from __future__ import annotations

import os

from celery import Celery
from dotenv import load_dotenv


load_dotenv()

app = Celery(
    "inrh_pipeline",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

app.autodiscover_tasks(["data_pipeline"])
