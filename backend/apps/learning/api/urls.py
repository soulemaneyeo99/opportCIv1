# ============================================
# apps/learning/api/urls.py
# ============================================
"""
OpportuCI - Learning API URLs
==============================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.learning.api.views import (
    LearningJourneyViewSet,
    MicroModuleViewSet,
    UserProgressViewSet
)

router = DefaultRouter()
router.register(r'journeys', LearningJourneyViewSet, basename='journey')
router.register(r'modules', MicroModuleViewSet, basename='module')
router.register(r'progress', UserProgressViewSet, basename='progress')

urlpatterns = [
    path('', include(router.urls)),
]


