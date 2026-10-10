from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from uuid import uuid4

from data_pipeline.celery_app import app
from data_pipeline.tasks import run_quality_pipeline_task
from .models import AnomalyLog, BatchMetadata, QualityScore


def home(request):
    selected_status = request.GET.get("status", "").strip()
    batches = BatchMetadata.objects.order_by("-started_at")
    if selected_status:
        batches = batches.filter(status=selected_status)

    latest = batches.first()
    scores = QualityScore.objects.filter(batch_id=latest.batch_id) if latest else []
    anomalies = (
        AnomalyLog.objects.filter(batch_id=latest.batch_id)
        .order_by("-severity", "source_type", "row_index")[:10]
        if latest
        else []
    )
    return render(request, "quality_dashboard/home.html", {
        "batches": batches[:20],
        "latest": latest,
        "scores": scores,
        "anomalies": anomalies,
        "selected_status": selected_status,
    })


def batch_detail(request, batch_id):
    batch = get_object_or_404(BatchMetadata, batch_id=batch_id)
    scores = QualityScore.objects.filter(batch_id=batch_id).order_by("source_type")
    anomalies = AnomalyLog.objects.filter(batch_id=batch_id)
    source = request.GET.get("source", "").strip()
    severity = request.GET.get("severity", "").strip()
    if source:
        anomalies = anomalies.filter(source_type=source)
    if severity:
        anomalies = anomalies.filter(severity=severity)
    return render(request, "quality_dashboard/batch_detail.html", {
        "batch": batch,
        "scores": scores,
        "anomalies": anomalies[:200],
        "source": source,
        "severity": severity,
    })


@require_POST
def start_pipeline(request):
    batch_id = f"batch_{uuid4().hex[:8]}"
    task = run_quality_pipeline_task.delay(batch_id)
    return redirect(f"/?pipeline_batch={batch_id}&task_id={task.id}")


@require_GET
def pipeline_status(request, batch_id):
    task_id = request.GET.get("task_id", "")
    batch = BatchMetadata.objects.filter(batch_id=batch_id).first()
    if batch is None:
        task_state = app.AsyncResult(task_id).state if task_id else "PENDING"
        return JsonResponse({
            "batch_id": batch_id,
            "status": "QUEUED",
            "task_state": task_state,
            "source_count": 0,
        })
    scores = list(QualityScore.objects.filter(batch_id=batch_id).values(
        "source_type", "global_score", "grade", "anomaly_count"
    ))
    return JsonResponse({
        "batch_id": batch.batch_id,
        "status": batch.status,
        "task_state": app.AsyncResult(task_id).state if task_id else batch.status,
        "source_count": batch.source_count,
        "scores": scores,
        "completed_at": batch.completed_at,
    })