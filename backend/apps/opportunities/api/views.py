"""
OpportuCI - Opportunities API Views
====================================
"""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from ..models import (
    Opportunity,
    OpportunityCategory,
    OpportunitySource,
    ApplicationTracker
)
from .serializers import (
    OpportunityListSerializer,
    OpportunityDetailSerializer,
    OpportunityCreateSerializer,
    OpportunityCategorySerializer,
    OpportunitySourceSerializer,
    ApplicationTrackerSerializer,
    ApplicationStatusUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly

import logging

logger = logging.getLogger(__name__)


class OpportunityCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour les catégories d'opportunités"""

    queryset = OpportunityCategory.objects.filter(is_active=True)
    serializer_class = OpportunityCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class OpportunitySourceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter les sources d'opportunités"""

    queryset = OpportunitySource.objects.filter(is_active=True)
    serializer_class = OpportunitySourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class OpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour les opportunités

    list: Liste les opportunités publiées
    retrieve: Détails d'une opportunité (incrémente les vues)
    create: Crée une nouvelle opportunité (authentifié)
    """

    queryset = Opportunity.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'opportunity_type', 'status', 'is_remote', 'education_level', 'featured']
    search_fields = ['title', 'description', 'organization', 'skills_required']
    ordering_fields = ['created_at', 'deadline', 'publication_date', 'view_count']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_queryset(self):
        """Filtre les opportunités selon le contexte"""
        queryset = super().get_queryset().select_related('category', 'source')

        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')

        if self.action == 'list':
            return queryset.filter(
                Q(status='published') | Q(created_by=self.request.user)
            ).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OpportunityCreateSerializer
        return OpportunityDetailSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """Incrémente le compteur de vues et calcule le score de matching"""
        instance = self.get_object()

        # Incrémenter les vues
        instance.view_count += 1
        instance.save(update_fields=['view_count'])

        # Enregistrer comme découverte si authentifié + calcul match score
        match_data = None
        if request.user.is_authenticated:
            tracker, created = ApplicationTracker.objects.get_or_create(
                user=request.user,
                opportunity=instance,
                defaults={'status': ApplicationTracker.Status.DISCOVERED}
            )

            # Calculer le score de matching si pas encore fait
            if tracker.ai_match_score is None:
                try:
                    from services.matching import OpportunityMatchingService
                    service = OpportunityMatchingService(use_ai=False)  # Heuristique rapide
                    match_result = service.calculate_match_for_application(
                        request.user, instance
                    )
                    tracker.ai_match_score = match_result['score']
                    tracker.ai_match_reasons = match_result['reasons']
                    tracker.save(update_fields=['ai_match_score', 'ai_match_reasons'])
                except Exception as e:
                    logger.warning(f"Erreur calcul match: {e}")

            match_data = {
                'score': tracker.ai_match_score,
                'reasons': tracker.ai_match_reasons,
                'status': tracker.status
            }

        serializer = self.get_serializer(instance)
        data = serializer.data
        if match_data:
            data['user_match'] = match_data
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save_opportunity(self, request, slug=None):
        """Sauvegarde une opportunité dans les favoris"""
        opportunity = self.get_object()

        tracker, created = ApplicationTracker.objects.get_or_create(
            user=request.user,
            opportunity=opportunity,
            defaults={'status': ApplicationTracker.Status.SAVED}
        )

        if not created and tracker.status == ApplicationTracker.Status.DISCOVERED:
            tracker.update_status(ApplicationTracker.Status.SAVED)

        return Response({
            'detail': 'Opportunité sauvegardée',
            'status': tracker.status
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unsave_opportunity(self, request, slug=None):
        """Retire une opportunité des favoris"""
        opportunity = self.get_object()

        tracker = ApplicationTracker.objects.filter(
            user=request.user,
            opportunity=opportunity,
            status=ApplicationTracker.Status.SAVED
        ).first()

        if tracker:
            tracker.update_status(ApplicationTracker.Status.DISCOVERED)
            return Response({'detail': 'Opportunité retirée des favoris'})

        return Response(
            {'detail': 'Opportunité non trouvée dans vos favoris'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_applied(self, request, slug=None):
        """Marque une candidature comme envoyée"""
        opportunity = self.get_object()

        if opportunity.is_expired:
            return Response(
                {'detail': 'Cette opportunité est expirée'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tracker, created = ApplicationTracker.objects.get_or_create(
            user=request.user,
            opportunity=opportunity,
            defaults={'status': ApplicationTracker.Status.APPLIED}
        )

        if not created:
            tracker.update_status(ApplicationTracker.Status.APPLIED)

        return Response({
            'detail': 'Candidature enregistrée',
            'tracker': ApplicationTrackerSerializer(tracker).data
        })

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Liste les opportunités mises en avant"""
        queryset = self.get_queryset().filter(
            featured=True,
            status='published'
        )[:10]

        serializer = OpportunityListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Liste les opportunités qui expirent bientôt (7 jours)"""
        now = timezone.now()
        deadline = now + timezone.timedelta(days=7)

        queryset = self.get_queryset().filter(
            status='published',
            deadline__gte=now,
            deadline__lte=deadline
        ).order_by('deadline')[:20]

        serializer = OpportunityListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_created(self, request):
        """Liste les opportunités créées par l'utilisateur"""
        queryset = Opportunity.objects.filter(created_by=request.user)
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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recommendations(self, request):
        """
        Obtient les recommandations personnalisées IA

        GET /api/opportunities/recommendations/?limit=10&type=scholarship
        """
        from services.matching import OpportunityMatchingService

        limit = int(request.query_params.get('limit', 10))
        opp_type = request.query_params.get('type')

        # Vérifier que l'utilisateur a un profil complet
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'Profil requis pour les recommandations',
                'detail': 'Complétez votre profil pour recevoir des recommandations'
            }, status=status.HTTP_400_BAD_REQUEST)

        profile = request.user.profile
        if not profile.skills and not profile.interests:
            return Response({
                'warning': 'Profil incomplet',
                'detail': 'Ajoutez vos compétences et intérêts pour de meilleures recommandations',
                'recommendations': []
            })

        # Obtenir les recommandations
        try:
            service = OpportunityMatchingService(use_ai=True)
            results = service.get_recommendations_for_user(
                user=request.user,
                limit=limit,
                opportunity_type=opp_type
            )

            # Sérialiser
            recommendations = []
            for item in results:
                opp_data = OpportunityListSerializer(
                    item['opportunity'],
                    context={'request': request}
                ).data
                recommendations.append({
                    'opportunity': opp_data,
                    'match_score': item['match_score'],
                    'match_reasons': item['match_reasons'],
                    'ai_enhanced': item.get('ai_enhanced', False)
                })

            return Response({
                'count': len(recommendations),
                'recommendations': recommendations
            })

        except Exception as e:
            logger.error(f"Erreur recommandations: {e}")
            return Response({
                'error': 'Erreur lors du calcul des recommandations',
                'recommendations': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApplicationTrackerViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour le suivi des candidatures

    list: Liste toutes les candidatures de l'utilisateur
    retrieve: Détails d'une candidature
    update: Mise à jour du statut/notes
    """

    serializer_class = ApplicationTrackerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'opportunity__category', 'opportunity__opportunity_type']
    ordering_fields = ['discovered_at', 'applied_at', 'ai_match_score']
    ordering = ['-discovered_at']

    def get_queryset(self):
        return ApplicationTracker.objects.filter(
            user=self.request.user
        ).select_related('opportunity', 'opportunity__category')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Met à jour le statut d'une candidature"""
        tracker = self.get_object()

        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes')

        tracker.update_status(new_status, notes)

        return Response({
            'detail': 'Statut mis à jour',
            'tracker': ApplicationTrackerSerializer(tracker).data
        })

    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Liste les opportunités sauvegardées"""
        queryset = self.get_queryset().filter(status=ApplicationTracker.Status.SAVED)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def applied(self, request):
        """Liste les candidatures envoyées"""
        queryset = self.get_queryset().filter(
            status__in=[
                ApplicationTracker.Status.APPLIED,
                ApplicationTracker.Status.INTERVIEWING,
                ApplicationTracker.Status.OFFER
            ]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des candidatures"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'saved': queryset.filter(status=ApplicationTracker.Status.SAVED).count(),
            'preparing': queryset.filter(status=ApplicationTracker.Status.PREPARING).count(),
            'applied': queryset.filter(status=ApplicationTracker.Status.APPLIED).count(),
            'interviewing': queryset.filter(status=ApplicationTracker.Status.INTERVIEWING).count(),
            'offers': queryset.filter(status=ApplicationTracker.Status.OFFER).count(),
            'accepted': queryset.filter(status=ApplicationTracker.Status.ACCEPTED).count(),
            'rejected': queryset.filter(status=ApplicationTracker.Status.REJECTED).count(),
        }

        return Response(stats)


# Backward compatibility alias
UserOpportunityViewSet = ApplicationTrackerViewSet
