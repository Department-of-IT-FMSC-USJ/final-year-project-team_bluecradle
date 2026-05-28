from django.apps import AppConfig

class AuditModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_module'

    def ready(self):
        import audit_module.signals # noqa: F401