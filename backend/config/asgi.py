"""
ASGI config for OpportuCI project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from config.middleware import JWTAuthMiddlewareStack  # ✅ Import custom
from apps.simulations.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(  # ✅ Utiliser custom middleware
        URLRouter(
            websocket_urlpatterns
        )
    ),
})