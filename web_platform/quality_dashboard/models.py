from django.db import models


class BatchMetadata(models.Model):
    batch_id = models.CharField(max_length=100, primary_key=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=20)
    source_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = "batch_metadata"


class QualityScore(models.Model):
    batch_id = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20)
    global_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2)
    validity_score = models.DecimalField(max_digits=5, decimal_places=2)
    uniqueness_score = models.DecimalField(max_digits=5, decimal_places=2)
    consistency_score = models.DecimalField(max_digits=5, decimal_places=2)
    anomaly_count = models.IntegerField()
    details = models.JSONField()

    class Meta:
        managed = False
        db_table = "quality_scores"


class AnomalyLog(models.Model):
    batch_id = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20)
    row_index = models.IntegerField()
    entity_id = models.CharField(max_length=100, null=True)
    rule = models.CharField(max_length=150)
    method = models.CharField(max_length=30)
    severity = models.CharField(max_length=20)
    message = models.TextField()

    class Meta:
        managed = False
        db_table = "anomaly_logs"