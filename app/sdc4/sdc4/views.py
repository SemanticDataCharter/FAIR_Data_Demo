"""
Project-level views.
"""
from django.shortcuts import render
from django.conf import settings
from django.urls import get_resolver
from django.apps import apps


def index(request):
    """
    Root index view - Table of Contents for all installed SDC4 apps.
    """
    # Get all installed apps
    installed_apps = settings.INSTALLED_APPS

    # Filter to get only our data model apps (exclude Django built-ins)
    django_builtin_apps = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'crispy_forms',
        'crispy_bootstrap5',
        'rest_framework',
        'django_htmx',
        'widget_tweaks',
    ]

    # Get data model apps
    data_apps = []
    for app in installed_apps:
        if app not in django_builtin_apps:
            # Try to get the app's URL namespace and verbose name
            app_name = app.split('.')[-1]  # Get last part of dotted path

            # Check if app has URLs registered
            try:
                resolver = get_resolver()
                # Try to find namespace for this app
                namespace = None
                for pattern in resolver.url_patterns:
                    if hasattr(pattern, 'namespace') and pattern.namespace == app_name:
                        namespace = app_name
                        break

                if namespace:
                    # Try to get the DataModel from the app to get description
                    dm_label = app_name.replace('_', ' ').title()
                    dm_description = 'SDC4 Data Model Application'

                    try:
                        # Try to import the DataModel from the app
                        app_config = apps.get_app_config(app_name)
                        models_module = app_config.models_module

                        if models_module and hasattr(models_module, 'DataModel'):
                            DataModel = models_module.DataModel
                            # Get the DM metadata from the model class
                            if hasattr(DataModel, 'DM_LABEL'):
                                dm_label = DataModel.DM_LABEL
                            if hasattr(DataModel, 'DM_DESCRIPTION'):
                                dm_description = DataModel.DM_DESCRIPTION
                    except Exception:
                        # If we can't get DM info, use defaults
                        pass

                    data_apps.append({
                        'name': app_name,
                        'title': dm_label,
                        'description': dm_description,
                        'namespace': namespace,
                    })
            except Exception:
                # If we can't resolve URLs, skip this app
                pass

    context = {
        'project_name': 'sdc4',
        'data_apps': data_apps,
    }

    return render(request, 'index.html', context)
