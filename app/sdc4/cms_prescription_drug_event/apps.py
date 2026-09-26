"""
Django app configuration for cms_prescription_drug_event.
"""
from django.apps import AppConfig


class Cms_prescription_drug_eventConfig(AppConfig):
    """App configuration for cms_prescription_drug_event."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cms_prescription_drug_event'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import cms_prescription_drug_event.signals  # noqa: F401
