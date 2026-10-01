from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from .models import BatchMetadata, QualityScore, AnomalyLog


def home(request):
    """Vue principale du Dashboard de Qualité & Gouvernance."""
    batches = BatchMetadata.objects.all().select_related('quality_score')[:10]
    recent_anomalies = AnomalyLog.objects.all().select_related('batch')[:15]

    # Statistiques globales
    stats = QualityScore.objects.aggregate(
        avg_global=Avg('global_score'),
        avg_comp=Avg('completeness_score'),
        avg_val=Avg('validity_score'),
        avg_uniq=Avg('uniqueness_score'),
        avg_cons=Avg('consistency_score'),
    )

    total_batches = BatchMetadata.objects.count()
    total_anomalies = AnomalyLog.objects.count()
    critical_anomalies = AnomalyLog.objects.filter(severity='CRITICAL').count()

    context = {
        'batches': batches,
        'recent_anomalies': recent_anomalies,
        'stats': stats,
        'total_batches': total_batches,
        'total_anomalies': total_anomalies,
        'critical_anomalies': critical_anomalies,
    }
    return render(request, 'quality_dashboard/home.html', context)


def batch_detail(request, batch_id):
    """Vue détaillée d'un lot avec toutes ses anomalies."""
    batch = get_object_or_404(BatchMetadata, batch_id=batch_id)
    anomalies = batch.anomalies.all()
    score = getattr(batch, 'quality_score', None)

    return render(request, 'quality_dashboard/batch_detail.html', {
        'batch': batch,
        'score': score,
        'anomalies': anomalies
    })
