"""SDC validator for this app.

The implementation is the shared, cross-app validator in
``sdc4_shared.utils.sdc_validator``. This module re-exports it so existing
imports (``from .utils.sdc_validator import SDCValidator``) keep working while
there is a single implementation used by both this app and the REST API.
"""
from sdc4_shared.utils.sdc_validator import (  # noqa: F401
    SDCValidator,
    ValidationResult,
    SDC4_NS,
    SDC4_SCHEMA_URL,
)
