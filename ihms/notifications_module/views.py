from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from accounts_module.permission import IsPHM
from .models import NotificationLog
from .serializers import NotificationLogSerializer, PushSubscriptionSerializer


class PushSubscribeView(APIView):
    """
    POST /api/notifications/subscribe/
    Receives the browser's push subscription object and saves it
    to the correct profile based on the user's role.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        subscription_data = serializer.validated_data
        user = request.user

        # Save to the correct profile based on role —
        # PHM_User and Parent both have push_subscription fields
        if hasattr(user, 'phm_profile'):
            user.phm_profile.push_subscription = subscription_data
            user.phm_profile.save(update_fields=['push_subscription'])

        elif hasattr(user, 'parent_profile'):
            user.parent_profile.push_subscription = subscription_data
            user.parent_profile.save(update_fields=['push_subscription'])

        else:
            # MOH Officers do not receive push notifications
            return Response(
                {'detail': 'Push notifications are not available for this role.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {'detail': 'Push subscription saved successfully.'},
            status=status.HTTP_201_CREATED
        )


class NotificationListView(APIView):
    """
    GET /api/notifications/
    Returns all notifications for the currently authenticated user,
    ordered by most recent first. Used to populate the bell dropdown.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = NotificationLog.objects.filter(
            recipient=request.user
        ).select_related('infant')

        serializer = NotificationLogSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/<pk>/read/
    Marks a single notification as read.
    Only the recipient can mark their own notifications as read.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(
            NotificationLog,
            pk=pk,
            recipient=request.user  # ensures users can only mark their own
        )

        notification.is_read = True
        notification.save(update_fields=['is_read'])

        serializer = NotificationLogSerializer(notification)
        return Response(serializer.data)
    
class SyncConfirmView(APIView):
    """
    POST /api/notifications/sync-confirm/
    Called by sync.js after a successful sync batch.
    Triggers a SYNC_CONFIRM push notification to the PHM.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        record_count = request.data.get('record_count', 0)
        if record_count > 0:
            from .tasks import send_sync_confirm
            send_sync_confirm.delay(request.user.id, record_count)
        return Response({'detail': 'ok'}, status=status.HTTP_200_OK)