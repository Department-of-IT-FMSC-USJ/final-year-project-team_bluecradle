from django.contrib import admin
from .models import ClinicSession, GrowthRecord, ImmunizationEvent, FHBAtomicEvent

@admin.register(ClinicSession)
class ClinicSessionAdmin(admin.ModelAdmin):
    list_display = ['phm', 'session_type', 'session_date', 'location', 'moh_division', 'is_synced']
    list_filter = ['session_type', 'moh_division', 'is_synced']


@admin.register(GrowthRecord)
class GrowthRecordAdmin(admin.ModelAdmin):
    list_display = ['infant', 'visit_date', 'weight_kg', 'height_cm', 'whz', 'who_classification']
    list_filter = ['who_classification']
    search_fields = ['infant__phn', 'infant__full_name']


@admin.register(ImmunizationEvent)
class ImmunizationEventAdmin(admin.ModelAdmin):
    list_display = ['infant', 'vaccine', 'dose_status', 'date_administered', 'is_defaulter']
    list_filter = ['vaccine', 'dose_status', 'is_defaulter']
    search_fields = ['infant__phn', 'infant__full_name']


@admin.register(FHBAtomicEvent)
class FHBAtomicEventAdmin(admin.ModelAdmin):
    list_display = ['phm', 'event_type', 'fhb_service_code', 'priority', 'event_timestamp', 'is_synced']
    list_filter = ['event_type', 'priority', 'is_synced', 'moh_division']
    search_fields = ['infant__phn', 'phm__full_name']