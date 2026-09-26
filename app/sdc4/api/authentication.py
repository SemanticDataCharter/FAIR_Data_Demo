"""API authentication classes."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticate requests using X-API-Key header.

    Looks up the key hash in the database and verifies it's active.
    """

    def authenticate(self, request):
        """Authenticate the request using API key in X-API-Key header."""
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return None  # Allow other authentication methods

        # Hash the provided key
        key_hash = APIKey.hash_key(api_key)

        # Look up in database
        try:
            key_obj = APIKey.objects.get(key_hash=key_hash)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

        if not key_obj.is_active:
            raise AuthenticationFailed('API key has been deactivated')

        # Record usage (async in production)
        key_obj.record_usage()

        # Return (user-like object, auth info)
        return (APIKeyUser(key_obj), api_key)

    def authenticate_header(self, request):
        """Return the WWW-Authenticate header value."""
        return 'X-API-Key'


class APIKeyUser:
    """
    Pseudo-user object for API key authentication.
    Provides user-like interface for DRF permissions.
    """

    def __init__(self, api_key: APIKey):
        self.api_key = api_key
        self.organization_name = api_key.organization_name
        self.contact_email = api_key.contact_email
        self.is_authenticated = True
        self.is_active = api_key.is_active

    def __str__(self):
        return f"APIKey:{self.organization_name}"

    @property
    def is_anonymous(self):
        """Return False since API key is authenticated."""
        return False
