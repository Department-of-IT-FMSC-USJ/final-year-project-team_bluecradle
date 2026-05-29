import logging
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def send_push_notification(notification_log_id):
    """
    Async delivery worker.
    Reads a NotificationLog record, sends the push, marks is_sent + sent_at.
    """
    from .models import NotificationLog
    from .utils import send_web_push

    try:
        notification = NotificationLog.objects.select_related(
            'recipient'
        ).get(id=notification_log_id)
    except NotificationLog.DoesNotExist:
        logger.error(f'NotificationLog {notification_log_id} not found')
        return

    success = send_web_push(
        user=notification.recipient,
        title=notification.title,
        body=notification.body,
    )

    if success:
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save(update_fields=['is_sent', 'sent_at'])
        logger.info(f'Push sent — NotificationLog {notification_log_id}')
    else:
        logger.warning(f'Push failed — NotificationLog {notification_log_id}')


@shared_task
def check_defaulters():
    """
    Daily scheduled task.
    Finds immunizations where is_defaulter=True.
    Fires DEFAULTER → PHM and VAC_REMINDER → Parent for each.
    """
    from clinic_module.models import ImmunizationEvent
    from accounts_module.models import Parent
    from .models import NotificationLog

    defaulted = ImmunizationEvent.objects.filter(
        is_defaulter=True,
        dose_status='DEFAULTED',
    ).select_related(
        'infant',
        'infant__registered_phm__user',
    )

    for event in defaulted:
        infant = event.infant
        vaccine_display = event.get_vaccine_display()
        days_overdue = event.defaulter_days_overdue or 0

        # ── DEFAULTER → PHM ──────────────────────────────────────────────────
        phm_user = infant.registered_phm.user

        # Avoid duplicate notifications — skip if one already sent today
        already_notified = NotificationLog.objects.filter(
            recipient=phm_user,
            notification_type=NotificationLog.NotificationType.DEFAULTER,
            infant=infant,
            created_at__date=timezone.now().date(),
        ).exists()

        if not already_notified:
            phm_notification = NotificationLog.objects.create(
                recipient=phm_user,
                notification_type=NotificationLog.NotificationType.DEFAULTER,
                title='Defaulter Alert',
                body=(
                    f'{infant.full_name} (PHN: {infant.phn}) — '
                    f'{vaccine_display} overdue by {days_overdue} days.'
                ),
                infant=infant,
            )
            send_push_notification.delay(phm_notification.id)

        # ── VAC_REMINDER → Parent ─────────────────────────────────────────────
        guardian = Parent.objects.filter(phn=infant.phn).first()

        if guardian:
            already_reminded = NotificationLog.objects.filter(
                recipient=guardian.user,
                notification_type=NotificationLog.NotificationType.VAC_REMINDER,
                infant=infant,
                created_at__date=timezone.now().date(),
            ).exists()

            if not already_reminded:
                parent_notification = NotificationLog.objects.create(
                    recipient=guardian.user,
                    notification_type=NotificationLog.NotificationType.VAC_REMINDER,
                    title='Vaccination Overdue',
                    body=(
                        f'{infant.full_name}\'s {vaccine_display} vaccination '
                        f'is overdue by {days_overdue} days. '
                        f'Please visit your nearest clinic as soon as possible.'
                    ),
                    infant=infant,
                )
                send_push_notification.delay(parent_notification.id)


@shared_task
def send_sync_confirm(user_id, record_count):
    """
    Called from the sync endpoint after successful processing.
    Fires a SYNC_CONFIRM notification to the PHM.
    """
    from .models import NotificationLog

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f'User {user_id} not found for sync confirm')
        return

    record_label = 'record' if record_count == 1 else 'records'
    notification = NotificationLog.objects.create(
        recipient=user,
        notification_type=NotificationLog.NotificationType.SYNC_CONFIRM,
        title='Sync Complete',
        body=f'{record_count} {record_label} successfully uploaded.',
        infant=None,
    )
    send_push_notification.delay(notification.id)