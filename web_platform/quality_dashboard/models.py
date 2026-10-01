from django.db import models


class BatchMetadata(models.Model):
    """Métadonnées sur un lot de données ingéré dans le Data Lake."""
    SOURCE_CHOICES = [
        ('VMS', 'VMS (Navires GPS)'),
        ('LOGBOOK', 'Logbook (Carnet de pêche)'),
        ('SALES', 'Sales (Criées / Ventes)'),
        ('ENV', 'ENV (Océanographie)'),
    ]

    batch_id = models.CharField(max_length=100, unique=True, verbose_name="ID du Lot")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="Source")
    file_path = models.CharField(max_length=255, verbose_name="Chemin Bronze")
    total_rows = models.IntegerField(default=0, verbose_name="Total Lignes")
    valid_rows = models.IntegerField(default=0, verbose_name="Lignes Valides")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ingestion")

    class Meta:
        verbose_name = "Lot de données"
        verbose_name_plural = "Lots de données"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_id} ({self.source_type})"


class QualityScore(models.Model):
    """Scores de qualité associés à un lot de données selon les 4 dimensions DAMA."""
    batch = models.OneToOneField(BatchMetadata, on_delete=models.CASCADE, related_name="quality_score")
    completeness_score = models.FloatField(verbose_name="Complétude (%)")
    validity_score = models.FloatField(verbose_name="Validité (%)")
    uniqueness_score = models.FloatField(verbose_name="Unicité (%)")
    consistency_score = models.FloatField(verbose_name="Cohérence (%)")
    global_score = models.FloatField(verbose_name="Score Global (%)")
    grade = models.CharField(max_length=30, verbose_name="Grade")
    status = models.CharField(max_length=20, default="PASSED", verbose_name="Statut")
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Score de Qualité"
        verbose_name_plural = "Scores de Qualité"

    def __str__(self):
        return f"Score {self.batch.batch_id} : {self.global_score}% ({self.grade})"


class AnomalyLog(models.Model):
    """Enregistrement d'une anomalie détectée par les règles ou les statistiques."""
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critique'),
        ('WARNING', 'Avertissement'),
        ('INFO', 'Information'),
    ]

    batch = models.ForeignKey(BatchMetadata, on_delete=models.CASCADE, related_name="anomalies")
    row_index = models.IntegerField(verbose_name="Ligne du fichier")
    entity_id = models.CharField(max_length=100, blank=True, verbose_name="Identifiant Entité")
    rule_violated = models.CharField(max_length=100, verbose_name="Règle enfreinte")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='WARNING')
    message = models.TextField(verbose_name="Description de l'anomalie")
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'anomalie"
        verbose_name_plural = "Journaux d'anomalies"
        ordering = ['-detected_at']

    def __str__(self):
        return f"[{self.severity}] {self.rule_violated} sur {self.entity_id}"
