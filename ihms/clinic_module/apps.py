from django.apps import AppConfig

class ClinicModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic_module'

    def ready(self):
        import clinic_module.signals  # noqa: F401