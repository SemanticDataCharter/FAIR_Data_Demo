"""
Django app configuration for brfss_respondent.
"""
from django.apps import AppConfig


class Brfss_respondentConfig(AppConfig):
    """App configuration for brfss_respondent."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'brfss_respondent'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import brfss_respondent.signals  # noqa: F401
