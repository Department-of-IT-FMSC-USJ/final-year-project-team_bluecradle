from rest_framework import serializers
from infants_module.models import Infant
from clinic_module.models import GrowthRecord, ClinicSession, ScheduledVaccination
from ml_module.models import MLRiskAssessment
from notifications_module.models import NotificationLog


class ParentInfantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infant
        fields = [
            'phn',
            'first_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'sex',
            'birth_weight_kg',
            'birth_length_cm',
            'birth_order',
            'moh_division',
        ]


class ParentGrowthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrowthRecord
        fields = [
            'id',
            'visit_date',
            'age_in_days',
            'weight_kg',
            'height_cm',
            'muac_mm',
            'whz',
            'waz',
            'haz',
            'who_classification',
            'bilateral_pitting_oedema',
        ]


class ParentMLRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLRiskAssessment
        fields = [
            'risk_level',
            'confidence_score',
            'prob_normal',
            'prob_mam',
            'prob_sam',
            'assessed_at',
        ]


class ParentClinicSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicSession
        fields = [
            'id',
            'session_date',
            'session_type',
            'location',
            'status',
        ]


class ParentScheduledVaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledVaccination
        fields = [
            'id',
            'vaccine_name',
            'due_date',
            'status',
            'date_given',
            'notes',
        ]


class ParentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'notification_type',
            'title',
            'body',
            'is_read',
            'created_at',
        ]


class ParentDashboardSerializer(serializers.Serializer):
    """
    Aggregates all data needed for the parent dashboard in one response.
    """
    infant = ParentInfantSerializer()
    latest_growth = ParentGrowthRecordSerializer()
    latest_ml = ParentMLRiskSerializer()
    next_clinic_session = ParentClinicSessionSerializer()
    unread_notification_count = serializers.IntegerField()
    next_vaccine = ParentScheduledVaccinationSerializer()