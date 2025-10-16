# opportunities/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from ..models import Opportunity, OpportunityCategory, UserOpportunity
from .serializers import (
    OpportunityListSerializer, OpportunityDetailSerializer, 
    OpportunityCreateUpdateSerializer, OpportunityCategorySerializer,
    UserOpportunitySerializer
)
from .permissions import IsOwnerOrReadOnly
from .filters import OpportunityFilter

class OpportunityCategoryViewSet(viewsets.ModelViewSet):
    queryset = OpportunityCategory.objects.filter(is_active=True)
    serializer_class = OpportunityCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['title', 'description', 'organization', 'tags']
    ordering_fields = ['created_at', 'deadline', 'publication_date', 'view_count']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filtrer les opportunités selon le statut de l'utilisateur"""
        queryset = super().get_queryset()
        
        # Si l'utilisateur est non authentifié, montrer uniquement les opportunités publiées
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Si c'est une action pour lister toutes les opportunités
        if self.action == 'list':
            # Montrer toutes les opportunités publiées + celles créées par l'utilisateur
            return queryset.filter(
                Q(status='published') | Q(creator=self.request.user)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OpportunityCreateUpdateSerializer
        return OpportunityDetailSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCreatorOrReadOnly()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        """Incrémenter le compteur de vues lors de la consultation"""
        instance = self.get_object()
        
        # Incrémenter le compteur de vues
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # Enregistrer la consultation si l'utilisateur est authentifié
        if request.user.is_authenticated:
            UserOpportunity.objects.get_or_create(
                user=request.user,
                opportunity=instance,
                relation_type='viewed'
            )
        
        # Mettre à jour le statut si nécessaire
        instance.update_status()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, slug=None):
        """Marquer une opportunité comme postulée"""
        opportunity = self.get_object()
        
        if opportunity.is_expired:
            return Response(
                {"detail": "Cette opportunité est expirée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer ou mettre à jour la relation
        user_opp, created = UserOpportunity.objects.update_or_create(
            user=request.user,
            opportunity=opportunity,
            relation_type='applied',
            defaults={'status': 'pending'}
        )
        
        # Incrémenter le compteur si c'est une nouvelle candidature
        if created:
            opportunity.application_count += 1
            opportunity.save(update_fields=['application_count'])
        
        return Response(
            {"detail": "Votre candidature a été enregistrée avec succès."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def save_opportunity(self, request, slug=None):
        """Sauvegarder une opportunité"""
        opportunity = self.get_object()
        
        user_opp, created = UserOpportunity.objects.get_or_create(
            user=request.user,
            opportunity=opportunity,
            relation_type='saved'
        )
        
        return Response(
            {"detail": "Opportunité sauvegardée avec succès."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unsave_opportunity(self, request, slug=None):
        """Supprimer une opportunité des favoris"""
        opportunity = self.get_object()
        
        deleted, _ = UserOpportunity.objects.filter(
            user=request.user,
            opportunity=opportunity,
            relation_type='saved'
        ).delete()
        
        if deleted:
            return Response({"detail": "Opportunité retirée des favoris."})
        return Response(
            {"detail": "Cette opportunité n'était pas dans vos favoris."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Récupérer les opportunités mises en avant"""
        queryset = self.get_queryset().filter(featured=True, status='published')
        serializer = OpportunityListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_opportunities(self, request):
        """Récupérer les opportunités créées par l'utilisateur"""
        queryset = Opportunity.objects.filter(creator=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = OpportunityListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = OpportunityListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

class UserOpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = UserOpportunitySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return UserOpportunity.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Récupérer les opportunités sauvegardées"""
        queryset = self.get_queryset().filter(relation_type='saved')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def applied(self, request):
        """Récupérer les opportunités postulées"""
        queryset = self.get_queryset().filter(relation_type='applied')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_relation(self, request):
        """Récupérer les opportunités par type de relation"""
        relation_type = request.query_params.get('type', None)
        
        if not relation_type:
            return Response(
                {"detail": "Le paramètre 'type' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(relation_type=relation_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# opportunities/permissions.py
from rest_framework import permissions

class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Permission qui autorise uniquement le créateur à modifier une opportunité.
    """
    def has_object_permission(self, request, view, obj):
        # Les permissions en lecture sont autorisées pour toute demande.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les permissions d'écriture sont réservées au créateur ou à l'admin.
        return obj.creator == request.user or request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission qui autorise uniquement le propriétaire à modifier.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user
