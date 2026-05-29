from rest_framework import serializers
from .models import ChatLog


class ChatLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatLog
        fields = [
            'id',
            'role',
            'infant',
            'user_message',
            'bot_response',
            'rag_chunks_used',
            'language',
            'created_at',
        ]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    """Validates incoming chat requests."""
    message = serializers.CharField(max_length=2000)
    infant_phn = serializers.CharField(max_length=20, required=False, allow_blank=True)
    language = serializers.ChoiceField(
        choices=['EN', 'SI', 'TA'],
        default='EN'
    )