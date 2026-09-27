"""
URL configuration for sdc4 project.
"""
import importlib
from django.apps import apps
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('docs/', include('core.urls', namespace='docs')),
    path('demo/', include('demo.urls', namespace='demo')),
    path('console/', include('console.urls', namespace='console')),
]

# Auto-discover URL patterns from installed DM apps
_SKIP_APPS = {
    'api', 'core', 'demo', 'console', 'generic_storage', 'sdc4_shared',
    'crispy_forms', 'crispy_bootstrap5', 'rest_framework',
    'django_htmx', 'widget_tweaks', 'allauth', 'whitenoise',
}
for _app_config in apps.get_app_configs():
    if _app_config.name.startswith('django.') or _app_config.name in _SKIP_APPS:
        continue
    if '.' in _app_config.name:  # skip nested third-party (allauth.account, etc.)
        continue
    try:
        _urls_mod = importlib.import_module(f'{_app_config.name}.urls')
        if hasattr(_urls_mod, 'app_name'):
            urlpatterns.append(
                path(f'{_app_config.name}/', include(f'{_app_config.name}.urls', namespace=_app_config.name))
            )
    except (ImportError, ModuleNotFoundError):
        pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
