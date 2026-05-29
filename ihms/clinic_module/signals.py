from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from infants_module.models import Infant
from .models import ScheduledVaccination
from .vaccination_schedule import VACCINATION_SCHEDULE

@receiver(post_save, sender=Infant)
def auto_populate_vaccinations(sender, instance, created, **kwargs):
    if not created:
        return

    # date_of_birth may arrive as a string — parse it safely
    dob = instance.date_of_birth
    if isinstance(dob, str):
        from datetime import datetime
        dob = datetime.strptime(dob, '%Y-%m-%d').date()

    vaccinations = [
        ScheduledVaccination(
            infant=instance,
            vaccine_name=vaccine_name,
            due_date=dob + timedelta(days=offset),
            status=ScheduledVaccination.Status.PENDING,
        )
        for vaccine_name, offset in VACCINATION_SCHEDULE
    ]

    ScheduledVaccination.objects.bulk_create(vaccinations)  