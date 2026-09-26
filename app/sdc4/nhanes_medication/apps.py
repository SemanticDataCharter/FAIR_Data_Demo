"""
Django app configuration for nhanes_medication.
"""
from django.apps import AppConfig


class Nhanes_medicationConfig(AppConfig):
    """App configuration for nhanes_medication."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nhanes_medication'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import nhanes_medication.signals  # noqa: F401
