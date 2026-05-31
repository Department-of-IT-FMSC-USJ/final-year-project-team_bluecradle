from celery import shared_task
from django.db import transaction


@shared_task(bind=True, max_retries=3)
def run_ml_risk_assessment(self, infant_phn, growth_record_id):
    """
    Triggered after a GrowthRecord is synced to PostgreSQL.
    Assembles the feature array and writes an MLRiskAssessment.
    """
    try:
        from infants_module.models import Infant
        from clinic_module.models import GrowthRecord
        from .models import MLRiskAssessment
        from .inference import run_inference

        infant = Infant.objects.get(phn=infant_phn)

        # Fetch all growth records for this infant ordered by visit date.
        # The LSTM needs the full sequence — not just the latest record.
        growth_records = GrowthRecord.objects.filter(
            infant=infant
        ).order_by('visit_date')

        # Need at least 2 visits for meaningful trajectory prediction.
        if growth_records.count() < 2:
            return {'status': 'skipped', 'reason': 'insufficient_visits'}

        result = run_inference(infant, growth_records)

        with transaction.atomic():
            MLRiskAssessment.objects.update_or_create(
                infant=infant,
                triggered_by_growth_record=growth_record_id,
                defaults={
                    'risk_level':                  result['risk_level'],
                    'confidence_score':            result['confidence_score'],
                    'prob_normal':                 result['prob_normal'],
                    'prob_mam':                    result['prob_mam'],
                    'prob_sam':                    result['prob_sam'],
                    'feature_snapshot':            {
                        'infant_phn':        infant_phn,
                        'growth_record_id':  growth_record_id,
                        'visit_count':       growth_records.count(),
                    },
                    'model_version': 'bluecradle_lstm_v1',
                }
            )

            # ── Notify PHM if risk is SAM or MAM ─────────────────────────
            if result['risk_level'] in ['SAM', 'MAM']:
                from notifications_module.models import NotificationLog
                from notifications_module.tasks import send_push_notification

                notification = NotificationLog.objects.create(
                    recipient=infant.registered_phm.user,
                    notification_type=NotificationLog.NotificationType.ML_RISK,
                    title=f'ML Risk Alert — {result["risk_level"]}',
                    body=(
                        f'{infant.full_name} (PHN: {infant.phn}) has been flagged as '
                        f'{result["risk_level"]} with {round(result["confidence_score"] * 100)}% confidence.'
                    ),
                    infant=infant,
                )
                send_push_notification.delay(notification.id)

                # ── Notify Parent if linked ───────────────────────────────
                try:
                    from accounts_module.models import Parent
                    parent = Parent.objects.filter(phn=infant.phn).first()
                    if parent:
                        parent_notification = NotificationLog.objects.create(
                            recipient=parent.user,
                            notification_type=NotificationLog.NotificationType.ML_RISK,
                            title=f'Health Alert — {infant.first_name}',
                            body=(
                                f'{infant.first_name}\'s recent growth measurements indicate a '
                                f'{"severe" if result["risk_level"] == "SAM" else "moderate"} '
                                f'nutritional risk. Please contact your PHM immediately.'
                            ),
                            infant=infant,
                        )
                        send_push_notification.delay(parent_notification.id)
                except Exception:
                    pass  # Don't fail the whole task if parent notification fails

        return {'status': 'success', 'risk_level': result['risk_level']}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)