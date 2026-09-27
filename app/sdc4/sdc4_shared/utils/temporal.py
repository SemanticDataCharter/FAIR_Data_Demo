"""
Temporal storage abstraction layer.

This module provides a factory function that returns the appropriate
temporal storage client based on configuration. Currently a placeholder
for future Enterprise profile implementation with SirixDB.

Usage:
    from sdc4_shared.utils.temporal import get_temporal_client

    client = get_temporal_client()
    if client:
        client.store_xml(database, resource, xml_content)
"""
from django.conf import settings
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future: from .sirix_client import SirixDBClient


def get_temporal_client() -> Optional[object]:
    """
    Factory function returning temporal storage client if enabled.

    Currently returns None as SirixDB integration is part of the
    future Enterprise profile implementation.

    Returns:
        SirixDBClient instance or None if disabled/not implemented

    Configuration (settings.py):
        SIRIX_ENABLED: True to enable temporal storage (default: False)

        When enabled (future):
            SIRIX_URL: SirixDB server URL
            SIRIX_DATABASE: Database name
            KEYCLOAK_URL: Keycloak server URL
            KEYCLOAK_REALM: Keycloak realm name
            KEYCLOAK_CLIENT_ID: OAuth client ID
            KEYCLOAK_CLIENT_SECRET: OAuth client secret
    """
    if not getattr(settings, 'SIRIX_ENABLED', False):
        return None

    # Future Enterprise profile implementation
    # from .sirix_client import SirixDBClient
    # return SirixDBClient(
    #     sirix_url=settings.SIRIX_URL,
    #     keycloak_url=settings.KEYCLOAK_URL,
    #     realm=settings.KEYCLOAK_REALM,
    #     client_id=settings.KEYCLOAK_CLIENT_ID,
    #     client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    # )

    raise NotImplementedError(
        "SirixDB temporal storage is not yet implemented. "
        "Set SIRIX_ENABLED=False or wait for Enterprise profile."
    )
