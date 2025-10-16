"""
ASGI config for OpportuCI project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Spécifiez le bon module de settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')

application = get_asgi_application()