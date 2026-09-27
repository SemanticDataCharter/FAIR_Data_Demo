"""
Django app configuration for cms_outpatient_claim.
"""
from django.apps import AppConfig


class Cms_outpatient_claimConfig(AppConfig):
    """App configuration for cms_outpatient_claim."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cms_outpatient_claim'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import cms_outpatient_claim.signals  # noqa: F401
