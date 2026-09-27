"""
SDC4 shared utility modules.

Provides:
- triplestore: Backend-agnostic triplestore client factory
- fuseki_client: Apache Jena Fuseki client implementation
- temporal: Temporal storage abstraction (for future Enterprise profile)
"""
from .triplestore import get_triplestore_client

__all__ = ['get_triplestore_client']
