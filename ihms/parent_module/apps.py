from django.apps import AppConfig


class ParentModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parent_module'
    verbose_name = 'Parent Module'