"""
Triplestore abstraction layer for backend-agnostic RDF operations.

This module provides a factory function that returns the appropriate
triplestore client based on configuration. Enterprise Stack uses GraphDB.

Usage:
    from sdc4_shared.utils.triplestore import get_triplestore_client

    client = get_triplestore_client()
    client.upload_graph(rdf_content, graph_uri)
"""
from django.conf import settings
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .graphdb_client import GraphDBClient


def get_triplestore_client() -> Optional['GraphDBClient']:
    """
    Factory function returning the appropriate triplestore client
    based on TRIPLESTORE_BACKEND setting.

    Enterprise Stack defaults to GraphDB for OWL 2 reasoning support.

    Returns:
        GraphDBClient: Configured triplestore client instance, or None if disabled

    Configuration (settings.py):
        TRIPLESTORE_BACKEND: 'graphdb' (default for Enterprise) or 'none'

        For GraphDB:
            GRAPHDB_URL: Base URL of GraphDB server
            GRAPHDB_REPOSITORY: Repository name
            GRAPHDB_USER: Admin username
            GRAPHDB_PASSWORD: Admin password
    """
    backend = getattr(settings, 'TRIPLESTORE_BACKEND', 'graphdb')

    if backend == 'none':
        # Triplestore disabled
        return None
    else:
        # Default to GraphDB (Enterprise Stack)
        from .graphdb_client import GraphDBClient
        return GraphDBClient(
            graphdb_url=getattr(settings, 'GRAPHDB_URL', None),
            repository=getattr(settings, 'GRAPHDB_REPOSITORY', None),
            username=getattr(settings, 'GRAPHDB_USER', None),
            password=getattr(settings, 'GRAPHDB_PASSWORD', None),
        )
