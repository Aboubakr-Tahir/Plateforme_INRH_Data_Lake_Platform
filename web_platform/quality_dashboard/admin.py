from django.contrib import admin
from .models import BatchMetadata, QualityScore, AnomalyLog

@admin.register(BatchMetadata)
class BatchMetadataAdmin(admin.ModelAdmin):
    list_display = ('batch_id', 'source_type', 'total_rows', 'valid_rows', 'created_at')
    list_filter = ('source_type', 'created_at')
    search_fields = ('batch_id',)

@admin.register(QualityScore)
class QualityScoreAdmin(admin.ModelAdmin):
    list_display = ('batch', 'global_score', 'grade', 'status', 'evaluated_at')
    list_filter = ('status', 'grade')

@admin.register(AnomalyLog)
class AnomalyLogAdmin(admin.ModelAdmin):
    list_display = ('batch', 'entity_id', 'rule_violated', 'severity', 'detected_at')
    list_filter = ('severity', 'rule_violated')
    search_fields = ('entity_id', 'rule_violated', 'message')
