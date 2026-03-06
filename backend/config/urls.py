# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from core.views import health_check, api_info

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health & Info
    path('api/health/', health_check, name='health_check'),
    path('api/', api_info, name='api_info'),

    # Core API endpoints
    path('api/accounts/', include('apps.accounts.api.urls')),
    path('api/opportunities/', include('apps.opportunities.api.urls')),
    path('api/prep/', include('apps.prep.api.urls')),
    path('api/notifications/', include('apps.notifications.api.urls')),
]