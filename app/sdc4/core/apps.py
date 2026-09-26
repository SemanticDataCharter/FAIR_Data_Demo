"""
Core app configuration for sdc4.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Utilities'
