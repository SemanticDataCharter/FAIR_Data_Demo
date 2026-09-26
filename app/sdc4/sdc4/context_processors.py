"""Expose the demo version to every template, read once from app/sdc4/VERSION."""
from django.conf import settings


def cordovaos_version(request):
    return {'cordovaos_version': settings.CORDOVAOS_VERSION}
