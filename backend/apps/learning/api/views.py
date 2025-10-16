"""
OpportuCI - Learning API Views
================================
Endpoints REST pour le système d'apprentissage
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from apps.learning.models import (
    PersonalizedLearningJourney,
    MicroLearningModule,
    UserModuleProgress,
    JourneyModule
)
from apps.learning.api.serializers import (
    LearningJourneySerializer,
    MicroModuleSerializer,
    UserProgressSerializer,
    JourneyCreateSerializer
)
from apps.learning.services.path_generator import LearningPathGenerator
from apps.learning.services.intelligence_service import OpportunityIntelligenceService
from apps.opportunities.models import Opportunity
from core.permissions import IsOwnerOrReadOnly

import logging

logger = logging.getLogger(__name__)


class LearningJourneyViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les parcours d'apprentissage personnalisés
    
    list: Récupère tous les parcours de l'utilisateur
    retrieve: Détails d'un parcours spécifique
    create: Crée un nouveau parcours pour une opportunité
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = LearningJourneySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'target_opportunity']
    ordering_fields = ['created_at', 'progress_percentage', 'success_probability']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PersonalizedLearningJourney.objects.filter(
            user=self.request.user
        ).select_related(
            'target_opportunity'
        ).prefetch_related(
            'learning_modules'
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return JourneyCreateSerializer
        return LearningJourneySerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crée un parcours d'apprentissage personnalisé
        
        POST /api/learning/journeys/
        {
            "opportunity_id": 123
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        opportunity_id = serializer.validated_data['opportunity_id']
        opportunity = get_object_or_404(Opportunity, id=opportunity_id, status='published')
        
        # Vérifier si journey existe déjà
        existing = PersonalizedLearningJourney.objects.filter(
            user=request.user,
            target_opportunity=opportunity
        ).first()
        
        if existing:
            return Response({
                'detail': 'Un parcours existe déjà pour cette opportunité',
                'journey': LearningJourneySerializer(existing).data
            }, status=status.HTTP_200_OK)
        
        # Générer le parcours
        generator = LearningPathGenerator()
        journey = generator.generate_journey(request.user, opportunity)
        
        if not journey:
            return Response({
                'error': 'Impossible de générer le parcours'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            LearningJourneySerializer(journey).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Démarre un parcours d'apprentissage
        
        POST /api/learning/journeys/{id}/start/
        """
        journey = self.get_object()
        
        if journey.status != 'not_started':
            return Response({
                'detail': 'Le parcours est déjà démarré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        journey.status = 'in_progress'
        journey.started_at = timezone.now()
        journey.save()
        
        return Response({
            'detail': 'Parcours démarré avec succès',
            'journey': LearningJourneySerializer(journey).data
        })
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Récupère la progression détaillée d'un parcours
        
        GET /api/learning/journeys/{id}/progress/
        """
        journey = self.get_object()
        
        # Modules avec progression
        journey_modules = JourneyModule.objects.filter(
            journey=journey
        ).select_related('module').order_by('order')
        
        modules_data = []
        for jm in journey_modules:
            modules_data.append({
                'id': jm.module.id,
                'title': jm.module.title,
                'skill': jm.module.skill_taught,
                'duration_minutes': jm.module.duration_minutes,
                'priority': jm.priority,
                'is_mandatory': jm.is_mandatory,
                'order': jm.order,
                'started': jm.started,
                'completed': jm.completed,
                'time_spent_minutes': jm.time_spent_minutes,
                'best_score': jm.best_score
            })
        
        return Response({
            'journey_id': journey.id,
            'progress_percentage': journey.progress_percentage,
            'hours_completed': journey.hours_completed,
            'total_hours': journey.total_estimated_hours,
            'modules': modules_data,
            'skill_gaps': journey.skill_gaps
        })
    
    @action(detail=False, methods=['get'])
    def my_active(self, request):
        """
        Récupère les parcours actifs de l'utilisateur
        
        GET /api/learning/journeys/my_active/
        """
        active_journeys = self.get_queryset().filter(
            status='in_progress'
        )
        
        serializer = self.get_serializer(active_journeys, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analyze_opportunity(self, request, pk=None):
        """
        Analyse une opportunité sans créer de parcours
        
        GET /api/learning/journeys/{opportunity_id}/analyze_opportunity/
        """
        opportunity = get_object_or_404(Opportunity, id=pk)
        
        intelligence_service = OpportunityIntelligenceService()
        intelligence = intelligence_service.analyze_opportunity(opportunity)
        
        if not intelligence:
            return Response({
                'error': 'Impossible d\'analyser cette opportunité'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Calculer le match score pour l'utilisateur
        match_score = intelligence_service.calculate_match_score(request.user, opportunity)
        prep_time = intelligence_service.get_recommended_preparation_time(request.user, opportunity)
        
        return Response({
            'opportunity_id': opportunity.id,
            'opportunity_title': opportunity.title,
            'required_skills': intelligence.extracted_skills,
            'difficulty_score': intelligence.difficulty_score,
            'estimated_preparation_hours': prep_time,
            'market_demand': intelligence.market_demand,
            'salary_range': intelligence.typical_salary_range_fcfa,
            'match_score': match_score,
            'recommendation': self._get_match_recommendation(match_score)
        })
    
    def _get_match_recommendation(self, score: float) -> str:
        """Génère une recommandation selon le score de match"""
        if score >= 0.8:
            return "Excellent match ! Tu es déjà bien préparé pour cette opportunité."
        elif score >= 0.6:
            return "Bon match. Un peu de préparation et tu seras prêt."
        elif score >= 0.4:
            return "Match moyen. Quelques compétences à développer."
        else:
            return "Cette opportunité nécessite une préparation importante."


class MicroModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour les micro-modules d'apprentissage
    
    list: Liste tous les modules disponibles
    retrieve: Détails d'un module spécifique
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MicroModuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['content_type', 'difficulty_level', 'skill_taught']
    search_fields = ['title', 'description', 'skill_taught']
    ordering_fields = ['duration_minutes', 'total_completions', 'average_score']
    
    def get_queryset(self):
        return MicroLearningModule.objects.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Démarre un module
        
        POST /api/learning/modules/{id}/start/
        """
        module = self.get_object()
        
        # Créer ou récupérer progression
        progress, created = UserModuleProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        
        if created or progress.status == 'not_started':
            progress.start_module()
        
        return Response({
            'detail': 'Module démarré',
            'progress': UserProgressSerializer(progress).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Marque un module comme complété
        
        POST /api/learning/modules/{id}/complete/
        {
            "score": 85,
            "time_spent_minutes": 12
        }
        """
        module = self.get_object()
        score = request.data.get('score', 100)
        time_spent = request.data.get('time_spent_minutes', module.duration_minutes)
        
        # Récupérer progression
        progress = get_object_or_404(
            UserModuleProgress,
            user=request.user,
            module=module
        )
        
        # Compléter
        progress.complete_module(score)
        progress.time_spent_minutes = time_spent
        progress.save()
        
        # Mettre à jour le journey si applicable
        self._update_journey_progress(request.user, module)
        
        return Response({
            'detail': 'Module complété avec succès',
            'progress': UserProgressSerializer(progress).data
        })
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """
        Met à jour la progression d'un module
        
        POST /api/learning/modules/{id}/update_progress/
        {
            "progress_percentage": 50,
            "time_spent_minutes": 5
        }
        """
        module = self.get_object()
        
        progress, created = UserModuleProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        
        if created:
            progress.start_module()
        
        progress_pct = request.data.get('progress_percentage', 0)
        time_spent = request.data.get('time_spent_minutes', 0)
        
        progress.update_progress(progress_pct, time_spent)
        
        return Response({
            'detail': 'Progression mise à jour',
            'progress': UserProgressSerializer(progress).data
        })
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """
        Récupère le contenu adaptatif du module
        
        GET /api/learning/modules/{id}/content/?network_type=4G
        """
        module = self.get_object()
        network_type = request.query_params.get('network_type', '4G')
        
        # Contenu adapté au réseau
        content = module.get_content_for_network(network_type)
        
        return Response({
            'module_id': module.id,
            'title': module.title,
            'content_type': module.content_type,
            'duration_minutes': module.duration_minutes,
            'network_optimized': network_type,
            'estimated_data_mb': module.estimated_data_mb,
            'content': content
        })
    
    def _update_journey_progress(self, user, module):
        """Met à jour la progression du journey si le module en fait partie"""
        journey_modules = JourneyModule.objects.filter(
            module=module,
            journey__user=user,
            journey__status='in_progress'
        ).select_related('journey')
        
        for jm in journey_modules:
            jm.completed = True
            jm.completed_at = timezone.now()
            jm.save()
            
            # Recalculer progression du journey
            jm.journey.update_progress()


class UserProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter la progression de l'utilisateur
    
    list: Liste toutes les progressions
    retrieve: Détails d'une progression spécifique
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProgressSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'module__skill_taught']
    ordering_fields = ['last_accessed', 'best_score', 'time_spent_minutes']
    
    def get_queryset(self):
        return UserModuleProgress.objects.filter(
            user=self.request.user
        ).select_related('module')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques globales de progression
        
        GET /api/learning/progress/stats/
        """
        from django.db.models import Sum, Avg, Count
        
        stats = self.get_queryset().aggregate(
            total_modules_started=Count('id'),
            total_modules_completed=Count('id', filter=models.Q(status='completed')),
            total_time_minutes=Sum('time_spent_minutes'),
            average_score=Avg('best_score', filter=models.Q(status='completed'))
        )
        
        # Learning streak
        streak_days = self._calculate_learning_streak(request.user)
        
        # Most practiced skill
        most_practiced = self.get_queryset().values('module__skill_taught').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        return Response({
            'total_modules_started': stats['total_modules_started'] or 0,
            'total_modules_completed': stats['total_modules_completed'] or 0,
            'total_hours_learned': round((stats['total_time_minutes'] or 0) / 60, 1),
            'average_score': round(stats['average_score'] or 0, 1),
            'learning_streak_days': streak_days,
            'most_practiced_skill': most_practiced['module__skill_taught'] if most_practiced else None
        })
    
    def _calculate_learning_streak(self, user) -> int:
        """Calcule la série de jours consécutifs d'apprentissage"""
        from datetime import timedelta
        
        activity_dates = UserModuleProgress.objects.filter(
            user=user,
            last_accessed__isnull=False
        ).dates('last_accessed', 'day', order='DESC')
        
        if not activity_dates:
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        for date in activity_dates:
            if date == current_date or date == current_date - timedelta(days=streak):
                streak += 1
            else:
                break
        
        return streak