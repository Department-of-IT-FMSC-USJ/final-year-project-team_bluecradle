from django.db import models
from django.contrib.auth import get_user_model
from infants_module.models import Infant

User = get_user_model()

class NotificationLog(models.Model):
    class NotificationType(models.TextChoices):
        DEFAULTER = 'DEFAULTER', 'Defaulter Alert'
        ML_RISK = 'ML_RISK', 'ML Risk Alert'
        SYNC_CONFIRM = 'SYNC_CONFIRM', 'Sync Confirmation'
        CLINIC_REMINDER = 'CLINIC_REMINDER', 'Clinic Reminder'
        VAC_REMINDER = 'VAC_REMINDER', 'Vaccination Reminder'

    recipient = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    infant = models.ForeignKey(
        Infant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.notification_type} → {self.recipient.username} | {self.title}'