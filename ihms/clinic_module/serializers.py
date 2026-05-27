from rest_framework import serializers
from .models import ClinicSession, GrowthRecord, ImmunizationEvent, FHBAtomicEvent
from .zscore_utils import classify_who, get_grace_period_days, is_defaulter
from datetime import date

class ClinicSessionSerializer(serializers.ModelSerializer):

    phm_name = serializers.CharField(
        source='phm.full_name',
        read_only=True
    )

    class Meta:
        model = ClinicSession
        fields = [
            'id',
            'phm',
            'phm_name',
            'session_date',
            'session_type',
            'location',
            'moh_division',
            'is_synced',
            'synced_at',
            'created_at',
        ]
        read_only_fields = [
            'phm',
            'moh_division',
            'is_synced',
            'synced_at',
            'created_at',
        ]


class GrowthRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = GrowthRecord
        fields = [
            'id',
            'infant',
            'session',
            'visit_date',
            'age_in_days',
            'weight_kg',
            'height_cm',
            'muac_mm',
            'bilateral_pitting_oedema',
            'whz',
            'waz',
            'haz',
            'who_classification',
            'days_since_last_visit',
            'weight_delta_kg',
            'whz_velocity',
            'created_at',
        ]
        read_only_fields = [
            'who_classification',
            'days_since_last_visit',
            'weight_delta_kg',
            'whz_velocity',
            'created_at',
        ]

    def validate(self, attrs):
        # Z-scores arrive from the device already calculated.
        # We validate that at least WHZ is present before
        # attempting WHO classification.
        if not attrs.get('whz') and not attrs.get('bilateral_pitting_oedema'):
            raise serializers.ValidationError(
                "Either WHZ score or bilateral pitting oedema flag must be provided."
            )
        return attrs

    def create(self, validated_data) -> GrowthRecord:
        infant = validated_data['infant']
        visit_date = validated_data['visit_date']

        # Step 1 — Apply WHO classification server-side.
        validated_data['who_classification'] = classify_who(
            whz=validated_data.get('whz'),
            muac_mm=float(validated_data['muac_mm']) if validated_data.get('muac_mm') else None,
            oedema=validated_data.get('bilateral_pitting_oedema', False)
        )

        # Step 2 — Calculate delta fields from previous GrowthRecord.
        previous = GrowthRecord.objects.filter(
            infant=infant
        ).order_by('-visit_date').first()

        if previous:
            validated_data['days_since_last_visit'] = (
                visit_date - previous.visit_date
            ).days
            validated_data['weight_delta_kg'] = (
                validated_data['weight_kg'] - previous.weight_kg
            )
            if previous.whz is not None and validated_data.get('whz') is not None:
                validated_data['whz_velocity'] = (
                    validated_data['whz'] - previous.whz
                )

        return super().create(validated_data)
    
class ImmunizationEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = ImmunizationEvent
        fields = [
            'id',
            'infant',
            'session',
            'vaccine',
            'dose_status',
            'date_administered',
            'batch_number',
            'adverse_event_noted',
            'adverse_event_details',
            'scheduled_date',
            'is_defaulter',
            'defaulter_days_overdue',
            'grace_period_days',
            'created_at',
        ]
        read_only_fields = [
            'is_defaulter',
            'defaulter_days_overdue',
            'grace_period_days',
            'created_at',
        ]

    def validate(self, attrs):
        dose_status = attrs.get('dose_status')

        # If administered, batch number and date are mandatory.
        if dose_status == 'ADMINISTERED':
            if not attrs.get('date_administered'):
                raise serializers.ValidationError(
                    "date_administered is required when dose_status is ADMINISTERED."
                )
            if not attrs.get('batch_number'):
                raise serializers.ValidationError(
                    "batch_number is required when dose_status is ADMINISTERED."
                )

        # If defaulted, scheduled_date is mandatory to calculate overdue days.
        if dose_status == 'DEFAULTED':
            if not attrs.get('scheduled_date'):
                raise serializers.ValidationError(
                    "scheduled_date is required when dose_status is DEFAULTED."
                )

        return attrs

    def create(self, validated_data):
        dose_status = validated_data.get('dose_status')
        infant = validated_data['infant']

        # Only calculate defaulter fields when dose is missed.
        if dose_status == 'DEFAULTED':
            scheduled_date = validated_data['scheduled_date']
            date_of_birth = infant.date_of_birth

            grace_period = get_grace_period_days(date_of_birth, scheduled_date)
            days_overdue = (date.today() - scheduled_date).days

            validated_data['grace_period_days'] = grace_period
            validated_data['is_defaulter'] = days_overdue > grace_period
            validated_data['defaulter_days_overdue'] = max(0, days_overdue - grace_period)

        return super().create(validated_data)
    
class FHBAtomicEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = FHBAtomicEvent
        fields = [
            'id',
            'infant',
            'session',
            'phm',
            'moh_division',
            'event_type',
            'fhb_service_code',
            'priority',
            'payload_json',
            'event_timestamp',
            'is_synced',
            'synced_at',
            'created_at',
        ]
        read_only_fields = [
            'phm',
            'moh_division',
            'is_synced',
            'synced_at',
            'created_at',
        ]