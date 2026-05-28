import hashlib
import json
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('SYNC', 'Sync'),
        ('DELETE_ATTEMPT', 'Delete Attempt')
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    payload_hash = models.CharField(max_length=64)
    payload_snapshot = models.JSONField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.timestamp} | {self.action} | {self.model_name} #{self.object_id}"
    
    # ── Immutability guards ──────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError(
                'AuditLog records are immutable and cannot be updated.'
            )
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('AuditLog records are immutable and cannot be deleted.')