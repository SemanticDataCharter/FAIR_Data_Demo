"""Expose the demo version to every template, read once from app/sdc4/VERSION."""
from django.conf import settings


def app_version(request):
    return {'app_version': settings.APP_VERSION}
