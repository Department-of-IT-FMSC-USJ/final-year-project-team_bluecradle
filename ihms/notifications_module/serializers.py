from rest_framework import serializers
from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    # Human-readable label for the notification type
    # e.g. "Defaulter Alert" instead of "DEFAULTER"
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    # Infant's full name — avoids the frontend needing a second request
    infant_name = serializers.CharField(
        source='infant.full_name',
        read_only=True
    )

    infant_phn = serializers.CharField(
        source='infant.phn',
        read_only=True
    )

    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'body',
            'infant',
            'infant_name',
            'infant_phn',
            'is_sent',
            'is_read',
            'sent_at',
            'created_at',
        ]
        # All fields are read-only except is_read —
        # the only thing the frontend ever writes is marking as read
        read_only_fields = [
            'notification_type',
            'notification_type_display',
            'title',
            'body',
            'infant',
            'infant_name',
            'infant_phn',
            'is_sent',
            'sent_at',
            'created_at',
        ]


class PushSubscriptionSerializer(serializers.Serializer):
    """
    Validates the push subscription object sent by the browser.
    The browser always sends exactly this structure after
    the user grants notification permission.
    """
    endpoint = serializers.URLField()
    keys = serializers.DictField()

    def validate_keys(self, value):
        # The browser must provide both p256dh and auth keys —
        # these are the encryption keys pywebpush needs to send the push
        if 'p256dh' not in value or 'auth' not in value:
            raise serializers.ValidationError(
                "Push subscription keys must contain both 'p256dh' and 'auth'."
            )
        return value