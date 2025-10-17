"""
OpportuCI - Simulations API Views
==================================
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from apps.simulations.models import (
    InterviewSimulation,
    ProfessionalTaskSimulation,
    UserTaskAttempt
)
from apps.simulations.api.serializers import (
    InterviewSimulationSerializer,
    InterviewSimulationDetailSerializer,
    InterviewSimulationCreateSerializer,
    InterviewMessageSerializer,
    ProfessionalTaskSerializer,
    ProfessionalTaskDetailSerializer,
    TaskGenerateSerializer,
    UserTaskAttemptSerializer,
    TaskSubmitSerializer
)
from apps.simulations.services.interview_simulator import InterviewSimulatorService
from apps.simulations.services.task_simulator import TaskSimulatorService
from apps.opportunities.models import Opportunity

import logging

logger = logging.getLogger(__name__)


class InterviewSimulationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les simulations d'entretien
    
    list: Liste toutes les simulations de l'utilisateur
    retrieve: Détails d'une simulation spécifique
    create: Crée une nouvelle simulation
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'interview_type', 'difficulty', 'opportunity']
    ordering_fields = ['created_at', 'overall_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return InterviewSimulation.objects.filter(
            user=self.request.user
        ).select_related('opportunity', 'opportunity__category')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InterviewSimulationDetailSerializer
        elif self.action == 'create':
            return InterviewSimulationCreateSerializer
        elif self.action == 'send_message':
            return InterviewMessageSerializer
        return InterviewSimulationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crée une nouvelle simulation d'entretien
        
        POST /api/simulations/interviews/
        {
            "opportunity_id": 123,
            "interview_type": "behavioral",
            "difficulty": "medium"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        opportunity_id = serializer.validated_data['opportunity_id']
        interview_type = serializer.validated_data.get('interview_type', 'behavioral')
        difficulty = serializer.validated_data.get('difficulty', 'medium')
        
        opportunity = get_object_or_404(Opportunity, id=opportunity_id, status='published')
        
        # Créer avec le service
        simulator = InterviewSimulatorService()
        simulation = simulator.create_simulation(
            user=request.user,
            opportunity=opportunity,
            interview_type=interview_type,
            difficulty=difficulty
        )
        
        if not simulation:
            return Response({
                'error': 'Impossible de créer la simulation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            InterviewSimulationSerializer(simulation).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Démarre une simulation
        
        POST /api/simulations/interviews/{id}/start/
        """
        simulation = self.get_object()
        
        if simulation.status != 'scheduled':
            return Response({
                'error': 'La simulation a déjà été démarrée ou terminée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Démarrer avec le service
        simulator = InterviewSimulatorService()
        first_message = simulator.start_simulation(simulation)
        
        return Response({
            'message': 'Simulation démarrée',
            'first_message': first_message,
            'simulation': InterviewSimulationDetailSerializer(simulation).data
        })
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Envoie un message dans la simulation
        
        POST /api/simulations/interviews/{id}/send_message/
        {
            "message": "Ma réponse..."
        }
        """
        simulation = self.get_object()
        
        if simulation.status != 'in_progress':
            return Response({
                'error': 'La simulation n\'est pas en cours'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['message']
        
        # Traiter avec le service
        simulator = InterviewSimulatorService()
        recruiter_response = simulator.process_user_response(simulation, user_message)
        
        # Rafraîchir pour avoir le statut à jour
        simulation.refresh_from_db()
        
        return Response({
            'recruiter_message': recruiter_response,
            'status': simulation.status,
            'conversation_length': len(simulation.conversation),
            'is_completed': simulation.status == 'completed'
        })
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Récupère les résultats détaillés de la simulation
        
        GET /api/simulations/interviews/{id}/results/
        """
        simulation = self.get_object()
        
        if simulation.status != 'completed':
            return Response({
                'error': 'La simulation n\'est pas terminée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'overall_score': simulation.overall_score,
            'detailed_scores': simulation.detailed_scores,
            'strengths': simulation.strengths,
            'improvements': simulation.improvements,
            'ai_feedback': simulation.ai_feedback,
            'recommended_practice': simulation.recommended_practice,
            'conversation': simulation.conversation,
            'duration_seconds': self._get_duration_seconds(simulation)
        })
    
    @action(detail=False, methods=['get'])
    def my_simulations(self, request):
        """
        Récupère toutes les simulations de l'utilisateur avec stats
        
        GET /api/simulations/interviews/my_simulations/
        """
        simulations = self.get_queryset()
        
        # Stats globales
        completed = simulations.filter(status='completed')
        avg_score = completed.aggregate(
            models.Avg('overall_score')
        )['overall_score__avg'] or 0
        
        serializer = self.get_serializer(simulations, many=True)
        
        return Response({
            'simulations': serializer.data,
            'stats': {
                'total': simulations.count(),
                'completed': completed.count(),
                'in_progress': simulations.filter(status='in_progress').count(),
                'average_score': round(avg_score, 1),
                'improvement_trend': self._calculate_improvement_trend(completed)
            }
        })
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """
        Termine manuellement une simulation
        
        POST /api/simulations/interviews/{id}/end/
        """
        simulation = self.get_object()
        
        if simulation.status != 'in_progress':
            return Response({
                'error': 'La simulation n\'est pas en cours'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Finaliser avec le service
        simulator = InterviewSimulatorService()
        simulator.finalize_interview(simulation)
        
        simulation.refresh_from_db()
        
        return Response({
            'message': 'Simulation terminée',
            'simulation': InterviewSimulationDetailSerializer(simulation).data
        })
    
    def _get_duration_seconds(self, simulation):
        """Calcule la durée totale"""
        if not simulation.started_at or not simulation.completed_at:
            return 0
        
        delta = simulation.completed_at - simulation.started_at
        return int(delta.total_seconds())
    
    def _calculate_improvement_trend(self, completed_simulations):
        """Calcule la tendance d'amélioration"""
        if completed_simulations.count() < 2:
            return 0
        
        recent = list(completed_simulations.order_by('-completed_at')[:5])
        if len(recent) < 2:
            return 0
        
        first_avg = sum(s.overall_score for s in recent[-2:]) / 2
        last_avg = sum(s.overall_score for s in recent[:2]) / 2
        
        return round(last_avg - first_avg, 1)


class ProfessionalTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les tâches professionnelles
    
    list: Liste les tâches disponibles
    retrieve: Détails d'une tâche
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'average_score', 'total_attempts']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ProfessionalTaskSimulation.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProfessionalTaskDetailSerializer
        elif self.action == 'generate':
            return TaskGenerateSerializer
        return ProfessionalTaskSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Génère une tâche personnalisée avec IA
        
        POST /api/simulations/tasks/generate/
        {
            "skill": "Excel",
            "difficulty": "intermediate"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        skill = serializer.validated_data['skill']
        difficulty = serializer.validated_data.get('difficulty', 'intermediate')
        
        # Générer avec le service
        simulator = TaskSimulatorService()
        task = simulator.generate_contextual_task(
            skill=skill,
            user=request.user,
            difficulty=difficulty
        )
        
        if not task:
            return Response({
                'error': 'Impossible de générer la tâche'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            ProfessionalTaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        """
        Démarre une tentative sur une tâche
        
        POST /api/simulations/tasks/{id}/start_attempt/
        """
        task = self.get_object()
        
        # Vérifier si tentative en cours
        existing = UserTaskAttempt.objects.filter(
            user=request.user,
            task=task,
            status='in_progress'
        ).first()
        
        if existing:
            return Response({
                'attempt': UserTaskAttemptSerializer(existing).data,
                'task': ProfessionalTaskDetailSerializer(task).data,
                'message': 'Tentative en cours reprise'
            })
        
        # Créer nouvelle tentative
        simulator = TaskSimulatorService()
        attempt = simulator.start_attempt(request.user, task)
        
        return Response({
            'attempt': UserTaskAttemptSerializer(attempt).data,
            'task': ProfessionalTaskDetailSerializer(task).data,
            'message': 'Tentative démarrée'
        }, status=status.HTTP_201_CREATED)


class UserTaskAttemptViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les tentatives de tâche
    
    list: Liste les tentatives de l'utilisateur
    retrieve: Détails d'une tentative
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserTaskAttemptSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'task__task_type']
    ordering_fields = ['started_at', 'score']
    ordering = ['-started_at']
    
    def get_queryset(self):
        return UserTaskAttempt.objects.filter(
            user=self.request.user
        ).select_related('task')
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Soumet le travail pour évaluation
        
        POST /api/simulations/attempts/{id}/submit/
        {
            "work_data": {
                "file_url": "...",
                "answers": {...}
            }
        }
        """
        attempt = self.get_object()
        
        if attempt.status != 'in_progress':
            return Response({
                'error': 'Cette tentative ne peut plus être modifiée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TaskSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        work_data = serializer.validated_data['work_data']
        
        # Soumettre avec le service
        simulator = TaskSimulatorService()
        simulator.submit_work(attempt, work_data)
        
        attempt.refresh_from_db()
        
        return Response({
            'message': 'Travail soumis et évalué',
            'attempt': UserTaskAttemptSerializer(attempt).data
        })
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Récupère les résultats détaillés
        
        GET /api/simulations/attempts/{id}/results/
        """
        attempt = self.get_object()
        
        if attempt.status != 'evaluated':
            return Response({
                'error': 'Tentative pas encore évaluée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'score': attempt.score,
            'detailed_scores': attempt.detailed_scores,
            'ai_feedback': attempt.ai_feedback,
            'mentor_feedback': attempt.mentor_feedback,
            'time_taken_minutes': attempt.time_taken_minutes,
            'time_limit_minutes': attempt.task.time_limit_minutes,
            'passed': attempt.score >= 70 if attempt.score else False
        })