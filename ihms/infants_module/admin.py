from django.contrib import admin
from .models import Infant

@admin.register(Infant)
class InfantAdmin(admin.ModelAdmin):
    list_display = ['phn', 'full_name', 'date_of_birth', 'sex', 'registered_phm', 'moh_division', 'created_at']
    search_fields = ['phn', 'first_name', 'last_name', 'full_name']
    list_filter = ['sex', 'moh_division', 'registered_phm']
    readonly_fields = ['phn', 'created_at', 'updated_at']