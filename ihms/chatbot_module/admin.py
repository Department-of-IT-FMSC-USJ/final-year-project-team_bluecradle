from django.contrib import admin
from .models import ChatLog

@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role', 'language', 'infant', 'created_at']
    list_filter = ['role', 'language', 'created_at']
    search_fields = ['user__username', 'user_message']
    readonly_fields = [
        'user', 'role', 'infant', 'user_message',
        'bot_response', 'rag_chunks_used', 'language', 'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False