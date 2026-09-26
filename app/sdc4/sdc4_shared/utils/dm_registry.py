"""
DM Registry - Scans installed apps to map dm_ct_id to Django models.

This utility scans all installed Django apps looking for models with
a DM_CT_ID class attribute, allowing dynamic routing of XML instances
to the correct model class.
"""

from django.apps import apps
from django.db import models
from typing import Optional, Dict


_registry_cache: Optional[Dict[str, type]] = None


def build_dm_registry() -> Dict[str, type]:
    """
    Build a registry mapping dm_ct_id to Django model classes.

    Scans all installed apps looking for models with DM_CT_ID attribute.

    Returns:
        dict: Mapping of dm_ct_id (str) to model class (type)

    Example:
        {
            'rb46xg2fk464oqmlmyejpn2j': <class 'testdata3.models.TestData3Instance'>,
            'abc123xyz789...': <class 'arrests.models.ArrestInstance'>,
        }
    """
    registry = {}

    # Iterate through all installed apps
    for app_config in apps.get_app_configs():
        # Skip Django built-in apps
        if app_config.name.startswith('django.'):
            continue

        # Skip our utility apps
        if app_config.name in ('api', 'generic_storage'):
            continue

        # Get all models in this app
        for model in app_config.get_models():
            # Check if model has DM_CT_ID attribute
            if hasattr(model, 'DM_CT_ID'):
                dm_ct_id = getattr(model, 'DM_CT_ID')
                if dm_ct_id:
                    registry[dm_ct_id] = model

    return registry


def get_dm_registry() -> Dict[str, type]:
    """
    Get the DM registry, using cache if available.

    Returns:
        dict: Mapping of dm_ct_id to model class
    """
    global _registry_cache

    if _registry_cache is None:
        _registry_cache = build_dm_registry()

    return _registry_cache


def invalidate_dm_registry():
    """
    Invalidate the registry cache.

    Call this after installing new apps or making changes to models.
    """
    global _registry_cache
    _registry_cache = None


def get_model_for_dm_ct_id(dm_ct_id: str) -> Optional[type]:
    """
    Get the Django model class for a given dm_ct_id.

    Args:
        dm_ct_id: The data model CT_ID

    Returns:
        Model class if found, None otherwise

    Example:
        >>> model = get_model_for_dm_ct_id('rb46xg2fk464oqmlmyejpn2j')
        >>> if model:
        ...     instance = model.objects.get(instance_id='i-abc123')
    """
    registry = get_dm_registry()
    return registry.get(dm_ct_id)


def get_instance_model_name(dm_ct_id: str) -> Optional[str]:
    """
    Get the model name for a given dm_ct_id.

    Args:
        dm_ct_id: The data model CT_ID

    Returns:
        Model name string if found, None otherwise

    Example:
        >>> get_instance_model_name('rb46xg2fk464oqmlmyejpn2j')
        'TestData3Instance'
    """
    model = get_model_for_dm_ct_id(dm_ct_id)
    if model:
        return model.__name__
    return None


def list_all_data_models() -> Dict[str, Dict[str, str]]:
    """
    List all registered data models with metadata.

    Returns:
        dict: Mapping of dm_ct_id to metadata dict

    Example:
        {
            'rb46xg2fk464oqmlmyejpn2j': {
                'model_name': 'TestData3Instance',
                'app_label': 'testdata3',
                'dm_label': 'TestData3',
            }
        }
    """
    registry = get_dm_registry()
    result = {}

    for dm_ct_id, model in registry.items():
        dm_label = getattr(model, 'DM_LABEL', model.__name__)

        result[dm_ct_id] = {
            'model_name': model.__name__,
            'app_label': model._meta.app_label,
            'dm_label': dm_label,
        }

    return result
