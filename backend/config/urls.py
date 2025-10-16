# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps (URLs vides pour l'instant)
    path('api/accounts/', include('apps.accounts.api.urls')),
    path('api/opportunities/', include('apps.opportunities.api.urls')),
    path('api/learning/', include('apps.learning.api.urls')),
    path('api/credibility/', include('apps.credibility.api.urls')),
    path('api/notifications/', include('apps.notifications.api.urls')),
]