from rest_framework import serializers
from .models import Infant

class InfantSerializer(serializers.ModelSerializer):
    # Read-only computed fields — not stored, derived for the response.
    registered_phm_name = serializers.CharField(
        source='registered_phm.full_name',
        read_only=True
    )

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
            'registered_phm',
            'registered_phm_name',
            'moh_division',
            'created_at',
            'updated_at',
        ]
        # PHM is set automatically from the authenticated user.
        # moh_division is copied from PHM_User at registration time.
        # Neither should be editable by the form.
        read_only_fields = [
            'registered_phm',
            'moh_division',
            'created_at',
            'updated_at',
        ]