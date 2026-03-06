"""
OpportuCI - Opportunities API URLs
===================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OpportunityViewSet,
    OpportunityCategoryViewSet,
    OpportunitySourceViewSet,
    ApplicationTrackerViewSet
)

router = DefaultRouter()
router.register(r'categories', OpportunityCategoryViewSet, basename='category')
router.register(r'sources', OpportunitySourceViewSet, basename='source')
router.register(r'applications', ApplicationTrackerViewSet, basename='application')
router.register(r'', OpportunityViewSet, basename='opportunity')

urlpatterns = [
    path('', include(router.urls)),
]
