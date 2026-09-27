"""
WSGI config for sdc4 project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sdc4.settings')

application = get_wsgi_application()
