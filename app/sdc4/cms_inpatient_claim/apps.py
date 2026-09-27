"""
Django app configuration for cms_inpatient_claim.
"""
from django.apps import AppConfig


class Cms_inpatient_claimConfig(AppConfig):
    """App configuration for cms_inpatient_claim."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cms_inpatient_claim'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import cms_inpatient_claim.signals  # noqa: F401
