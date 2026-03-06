# backend/credibility/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from ..models import (
    Badge, Achievement, UserBadge, UserAchievement,
    CredibilityPoints, PointsHistory
)
from .serializers import (
    BadgeSerializer, AchievementSerializer, UserBadgeSerializer,
    UserAchievementSerializer, CredibilityPointsSerializer, PointsHistorySerializer
)
from .permissions import IsOwnerOrAdmin


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class UserBadgeViewSet(viewsets.ModelViewSet):
    serializer_class = UserBadgeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['badge']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Les administrateurs peuvent voir toutes les badges
            return UserBadge.objects.all()
        elif user.is_authenticated:
            # Les utilisateurs connectés peuvent voir leurs propres badges
            return UserBadge.objects.filter(user=user)
        # Utilisateurs anonymes ne peuvent rien voir
        return UserBadge.objects.none()
    
    def get_permissions(self):
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_badges(self, request):
        badges = UserBadge.objects.filter(user=request.user)
        serializer = self.get_serializer(badges, many=True)
        return Response(serializer.data)


class UserAchievementViewSet(viewsets.ModelViewSet):
    serializer_class = UserAchievementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['achievement']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserAchievement.objects.all()
        elif user.is_authenticated:
            return UserAchievement.objects.filter(user=user)
        return UserAchievement.objects.none()
    
    def get_permissions(self):
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_achievements(self, request):
        achievements = UserAchievement.objects.filter(user=request.user)
        serializer = self.get_serializer(achievements, many=True)
        return Response(serializer.data)


class CredibilityPointsViewSet(viewsets.ModelViewSet):
    serializer_class = CredibilityPointsSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CredibilityPoints.objects.all()
        elif user.is_authenticated:
            return CredibilityPoints.objects.filter(user=user)
        return CredibilityPoints.objects.none()
    
    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_points(self, request):
        try:
            points = CredibilityPoints.objects.get(user=request.user)
            serializer = self.get_serializer(points)
            return Response(serializer.data)
        except CredibilityPoints.DoesNotExist:
            # Créer une nouvelle entrée si elle n'existe pas
            points = CredibilityPoints.objects.create(user=request.user)
            serializer = self.get_serializer(points)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def leaderboard(self, request):
        # Récupérer le top 10 des utilisateurs avec le plus de points
        top_users = CredibilityPoints.objects.all().order_by('-points')[:10]
        serializer = self.get_serializer(top_users, many=True)
        return Response(serializer.data)


class PointsHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = PointsHistorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source', 'operation']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return PointsHistory.objects.all()
        elif user.is_authenticated:
            return PointsHistory.objects.filter(user=user)
        return PointsHistory.objects.none()
    
    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_history(self, request):
        history = PointsHistory.objects.filter(user=request.user)
        
        # Pagination
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
