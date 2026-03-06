# backend/credibility/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BadgeViewSet, AchievementViewSet, UserBadgeViewSet,
    UserAchievementViewSet, CredibilityPointsViewSet, PointsHistoryViewSet
)

router = DefaultRouter()
router.register(r'badges', BadgeViewSet)
router.register(r'achievements', AchievementViewSet)
router.register(r'user-badges', UserBadgeViewSet, basename='user-badge')
router.register(r'user-achievements', UserAchievementViewSet, basename='user-achievement')
router.register(r'points', CredibilityPointsViewSet, basename='credibility-points')
router.register(r'points-history', PointsHistoryViewSet, basename='points-history')

urlpatterns = [
    path('', include(router.urls)),
]

