"""
OpportuCI - Account Views
==========================
"""
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    ProfilePictureUploadSerializer,
    CVUploadSerializer,
)
from ..models import User, Profile
from .permissions import IsOwnerOrReadOnly, IsAdminOrSelf

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Inscription des utilisateurs"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response(
                UserDetailSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour les utilisateurs"""
    queryset = User.objects.all().select_related('profile')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'upload_profile_picture':
            return ProfilePictureUploadSerializer
        elif self.action in ['profile', 'update_profile']:
            return ProfileSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrSelf()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer l'utilisateur connecté"""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Mettre à jour l'utilisateur connecté"""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(request.user).data)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        serializer = ProfileSerializer(request.user.profile, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Mettre à jour le profil"""
        serializer = ProfileUpdateSerializer(
            request.user.profile,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(request.user.profile).data)

    @action(detail=False, methods=['post'])
    def upload_profile_picture(self, request):
        """Télécharger une photo de profil"""
        serializer = ProfilePictureUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()

        user.profile_picture = serializer.validated_data['profile_picture']
        user.save()

        return Response(UserDetailSerializer(user).data)

    @action(detail=False, methods=['post'])
    def upload_cv(self, request):
        """Télécharger un CV"""
        serializer = CVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = request.user.profile
        if profile.cv:
            profile.cv.delete()

        profile.cv = serializer.validated_data['cv']
        profile.save()

        return Response(ProfileSerializer(profile).data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour le login avec infos utilisateur"""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Ajouter les infos utilisateur à la réponse
        data['user'] = UserDetailSerializer(self.user).data
        return data


class UserLoginView(TokenObtainPairView):
    """Connexion des utilisateurs"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
