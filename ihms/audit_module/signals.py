import json
import hashlib
from django.forms.models import model_to_dict
from .models import AuditLog
from django.dispatch import receiver
from infants_module.models import Infant
from clinic_module.models import ClinicSession, GrowthRecord, ImmunizationEvent, FHBAtomicEvent
from django.db.models.signals import post_save

def _compute_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

def _write_audit(instance, created, bool):
    action = 'CREATE' if created else 'UPDATE'
    snapshot = model_to_dict(instance)

    # model_to_dict skips non-editable fields like auto_now_add timestamps so we add pk and any timestamp manually
    snapshot['id'] = instance.pk

    if hasattr(instance, 'created_at'):
        snapshot['created_at'] = instance.created_at

    if hasattr(instance, 'updated_at'):
        snapshot['updated_at'] = instance.updated_at

    payload_hash = _compute_hash(snapshot)

    AuditLog.objects.create(
        actor=None,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        payload_hash=payload_hash,
        payload_snapshot=snapshot,
        ip_address=None
    )

@receiver(post_save, sender=Infant)
def audit_infant(sender, instance, created, **kwargs):
    _write_audit(instance, created)

@receiver(post_save, sender=ClinicSession)
def audit_clinic_session(sender, instance, created, **kwargs):
    _write_audit(instance, created)

@receiver(post_save, sender=GrowthRecord)
def audit_growth_record(sender, instance, created, **kwargs):
    _write_audit(instance, created)

@receiver(post_save, sender=ImmunizationEvent)
def audit_immunization_event(sender, instance, created, **kwargs):
    _write_audit(instance, created)

@receiver(post_save, sender=FHBAtomicEvent)
def audit_fhb_atomic_event(sender, instance, created, **kwargs):
    _write_audit(instance, created)