from django.db import models

# Create your models here.
from django.db import models
from infants_module.models import Infant


class MLRiskAssessment(models.Model):

    RISK_LEVEL_CHOICES = [
        ('NORMAL', 'Normal'),
        ('MAM', 'Moderate Acute Malnutrition Risk'),
        ('SAM', 'Severe Acute Malnutrition Risk'),
    ]

    infant = models.ForeignKey(
        Infant,
        on_delete=models.PROTECT,
        related_name='risk_assessments'
    )

    # Risk output from the LSTM model.
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)

    # Raw probability outputs from softmax layer.
    prob_normal = models.DecimalField(max_digits=5, decimal_places=4)
    prob_mam = models.DecimalField(max_digits=5, decimal_places=4)
    prob_sam = models.DecimalField(max_digits=5, decimal_places=4)

    # Snapshot of the feature array used for this prediction.
    # Stored for audit and reproducibility.
    feature_snapshot = models.JSONField()

    # Which model version produced this result.
    model_version = models.CharField(max_length=50, default='bluecradle_lstm_v1')

    # The GrowthRecord that triggered this assessment.
    triggered_by_growth_record = models.PositiveIntegerField()

    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at']
        # One assessment per growth record — no duplicates.
        unique_together = ['infant', 'triggered_by_growth_record']

    def __str__(self):
        return f"{self.infant} — {self.risk_level} — {self.assessed_at}"