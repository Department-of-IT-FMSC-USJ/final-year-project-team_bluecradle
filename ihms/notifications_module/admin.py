from django.contrib import admin
from .models import NotificationLog

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'recipient',
        'notification_type',
        'title',
        'infant',
        'is_sent',
        'is_read',
        'sent_at',
        'created_at',
    ]

    list_filter = [
        'notification_type',
        'is_sent',
        'is_read',
    ]

    search_fields = [
        'recipient__email',
        'recipient__username',
        'title',
        'infant__phn',
        'infant__full_name',
    ]

    readonly_fields = [
        'recipient',
        'notification_type',
        'title',
        'body',
        'infant',
        'is_sent',
        'is_read',
        'sent_at',
        'created_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False