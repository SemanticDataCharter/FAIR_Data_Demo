"""
Django app configuration for cms_beneficiary.
"""
from django.apps import AppConfig


class Cms_beneficiaryConfig(AppConfig):
    """App configuration for cms_beneficiary."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cms_beneficiary'

    def ready(self):
        """
        Import signals when app is ready.

        This ensures that signal handlers are registered when Django starts.
        """
        import cms_beneficiary.signals  # noqa: F401
