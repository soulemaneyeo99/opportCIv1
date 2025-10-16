# backend/formations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, FormationViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'formations', FormationViewSet)
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('', include(router.urls)),
]