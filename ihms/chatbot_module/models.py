from django.db import models
from django.conf import settings

class ChatLog(models.Model):
    class Role(models.TextChoices):
        PHM = 'PHM', 'PHM'
        PARENT = 'PARENT', 'Parent'

    class Language(models.TextChoices):
        EN = 'EN', 'English'
        SI = 'SI', 'Sinhala'
        TA = 'TA', 'Tamil'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chat_logs'
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    infant = models.ForeignKey(
        'infants_module.Infant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_logs'
    )
    user_message = models.TextField()
    bot_response = models.TextField()
    rag_chunks_used = models.JSONField(null=True, blank=True)
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.EN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} | {self.user} | {self.created_at:%Y-%m-%d %H:%M}"