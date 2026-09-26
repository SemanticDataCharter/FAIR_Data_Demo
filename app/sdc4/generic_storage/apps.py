"""Generic storage app configuration."""

from django.apps import AppConfig


class GenericStorageConfig(AppConfig):
    """Configuration for the generic storage app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'generic_storage'
    verbose_name = 'Generic Instance Storage'
