"""
Django app configuration for nhanes_participant.
"""
from django.apps import AppConfig


class Nhanes_participantConfig(AppConfig):
    """App configuration for nhanes_participant."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nhanes_participant'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import nhanes_participant.signals  # noqa: F401
