# opportunities/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet, OpportunityCategoryViewSet, UserOpportunityViewSet

router = DefaultRouter()
router.register(r'categories', OpportunityCategoryViewSet)
router.register(r'', OpportunityViewSet)
router.register(r'user-relations', UserOpportunityViewSet, basename='user-opportunity')

urlpatterns = [
    path('', include(router.urls)),
]