#backend/accounts/views.py
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
import base64

from .serializers import (
    UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    ProfilePictureUploadSerializer, UserProfileSerializer
)
from ..models import User, UserProfile
from .permissions import IsOwnerOrReadOnly, IsAdminOrSelf

class RegisterView(generics.CreateAPIView):
    """Vue pour l'inscription des utilisateurs avec gestion des fichiers"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Gestion spéciale pour le format multipart/form-data
        if request.content_type.startswith('multipart/form-data'):
            data = request.data.copy()
            if 'cv' in data and isinstance(data['cv'], str) and data['cv'].startswith('data:'):
                # Décoder le fichier base64 si envoyé en string
                format, file_str = data['cv'].split(';base64,')
                ext = format.split('/')[-1]
            data['cv'] = ContentFile(base64.b64decode(file_str), name=f'cv.{ext}')
        else:
            data = request.data

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('profile')
    filterset_fields = ['user_type', 'is_verified', 'city', 'education_level']
    search_fields = [
        'email', 'username', 'first_name', 'last_name',
        'profile__skills', 'profile__languages'
    ]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['created_at', 'last_login', 'username']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'upload_profile_picture':
            return ProfilePictureUploadSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrSelf()]
        elif self.action in ['me', 'update_me', 'upload_profile_picture', 'profile', 'update_profile']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres avancés
        education_level = self.request.query_params.get('education_level')
        if education_level:
            queryset = queryset.filter(education_level=education_level)
            
        skills = self.request.query_params.get('skills')
        if skills:
            queryset = queryset.filter(
                profile__skills__icontains=skills
            )
            
        languages = self.request.query_params.get('languages')
        if languages:
            queryset = queryset.filter(
                profile__languages__icontains=languages
            )
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer les informations complètes de l'utilisateur connecté"""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Mettre à jour les informations de base de l'utilisateur"""
        user = request.user
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Récupérer le profil complet de l'utilisateur"""
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Mettre à jour le profil utilisateur"""
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def upload_profile_picture(self, request):
        """Télécharger une photo de profil avec gestion des erreurs améliorée"""
        serializer = ProfilePictureUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()
        
        user.profile_picture = serializer.validated_data['profile_picture']
        user.save()
        
        return Response(
            UserDetailSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['delete'])
    def remove_profile_picture(self, request):
        """Supprimer la photo de profil avec gestion des erreurs"""
        user = request.user
        if not user.profile_picture:
            return Response(
                {'detail': 'Aucune photo de profil à supprimer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile_picture.delete()
        user.profile_picture = None
        user.save()
        
        return Response(
            {'detail': 'Photo de profil supprimée avec succès'},
            status=status.HTTP_204_NO_CONTENT
        )

class UserLoginSerializer(TokenObtainPairSerializer):
    """Sérialiseur personnalisé pour le login avec plus de détails"""
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        
        # Ajouter les infos utiles à la réponse
        user_data = UserDetailSerializer(self.user).data
        data.update({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        })
        return data

class UserLoginView(TokenObtainPairView):
    """Vue personnalisée pour la connexion des utilisateurs"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Vérifier si le compte est vérifié
        user = User.objects.get(email=request.data.get('email'))
        if not user.is_verified:
            return Response(
                {'detail': 'Compte non vérifié. Veuillez vérifier votre email.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return response