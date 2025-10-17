"""
OpportuCI - Simulations API URLs
=================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.simulations.api.views import (
    InterviewSimulationViewSet,
    ProfessionalTaskViewSet,
    UserTaskAttemptViewSet
)

router = DefaultRouter()
router.register(r'interviews', InterviewSimulationViewSet, basename='interview')
router.register(r'tasks', ProfessionalTaskViewSet, basename='task')
router.register(r'attempts', UserTaskAttemptViewSet, basename='attempt')

urlpatterns = [
    path('', include(router.urls)),
]