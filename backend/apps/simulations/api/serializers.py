"""
OpportuCI - Simulations API Serializers
========================================
"""
from rest_framework import serializers
from apps.simulations.models import (
    InterviewSimulation,
    ProfessionalTaskSimulation,
    UserTaskAttempt
)
from apps.opportunities.api.serializers import OpportunityListSerializer
from apps.learning.api.serializers import MicroModuleSerializer


class InterviewSimulationSerializer(serializers.ModelSerializer):
    """Serializer pour les simulations d'entretien"""
    
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    opportunity_organization = serializers.CharField(source='opportunity.organization', read_only=True)
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    elapsed_time_seconds = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = InterviewSimulation
        fields = [
            'id', 'user', 'opportunity', 'opportunity_title', 'opportunity_organization',
            'interview_type', 'interview_type_display', 'difficulty', 'difficulty_display',
            'duration_minutes', 'company_context', 'status', 'status_display',
            'overall_score', 'detailed_scores', 'ai_feedback', 'strengths', 'improvements',
            'recommended_practice', 'elapsed_time_seconds', 'progress_percentage',
            'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'company_context', 'overall_score', 'detailed_scores',
            'ai_feedback', 'strengths', 'improvements', 'recommended_practice',
            'created_at', 'started_at', 'completed_at'
        ]
    
    def get_elapsed_time_seconds(self, obj):
        """Temps écoulé depuis le début"""
        if not obj.started_at:
            return 0
        
        from django.utils import timezone
        if obj.completed_at:
            delta = obj.completed_at - obj.started_at
        else:
            delta = timezone.now() - obj.started_at
        
        return int(delta.total_seconds())
    
    def get_progress_percentage(self, obj):
        """Pourcentage de progression (basé sur nb de messages)"""
        if obj.status == 'completed':
            return 100
        
        # Estimation : ~10 échanges pour un entretien complet
        expected_messages = 20  # 10 questions/réponses
        current_messages = len(obj.conversation)
        
        return min(int((current_messages / expected_messages) * 100), 99)


class InterviewSimulationDetailSerializer(InterviewSimulationSerializer):
    """Serializer détaillé avec conversation complète"""
    
    conversation = serializers.JSONField(read_only=True)
    follow_up_modules = MicroModuleSerializer(many=True, read_only=True)
    
    class Meta(InterviewSimulationSerializer.Meta):
        fields = InterviewSimulationSerializer.Meta.fields + [
            'conversation', 'follow_up_modules'
        ]


class InterviewSimulationCreateSerializer(serializers.Serializer):
    """Serializer pour créer une simulation"""
    
    opportunity_id = serializers.IntegerField(required=True)
    interview_type = serializers.ChoiceField(
        choices=InterviewSimulation.INTERVIEW_TYPES,
        default='behavioral'
    )
    difficulty = serializers.ChoiceField(
        choices=InterviewSimulation.DIFFICULTY_LEVELS,
        default='medium'
    )
    
    def validate_opportunity_id(self, value):
        """Valide que l'opportunité existe"""
        from apps.opportunities.models import Opportunity
        
        if not Opportunity.objects.filter(id=value, status='published').exists():
            raise serializers.ValidationError("Opportunité introuvable ou non publiée")
        
        return value


class InterviewMessageSerializer(serializers.Serializer):
    """Serializer pour envoyer un message dans l'entretien"""
    
    message = serializers.CharField(required=True, min_length=1, max_length=2000)


class ProfessionalTaskSerializer(serializers.ModelSerializer):
    """Serializer pour les tâches professionnelles"""
    
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    estimated_data_usage = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfessionalTaskSimulation
        fields = [
            'id', 'title', 'task_type', 'task_type_display', 'description',
            'scenario', 'company_context', 'objectives', 'deliverables',
            'evaluation_criteria', 'time_limit_minutes', 'difficulty',
            'difficulty_display', 'points_reward', 'total_attempts',
            'average_score', 'average_completion_time', 'is_active',
            'estimated_data_usage', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_attempts', 'average_score', 'average_completion_time',
            'created_at'
        ]
    
    def get_estimated_data_usage(self, obj):
        """Estimation de la consommation data"""
        # Base : 1MB pour le texte/description
        base_mb = 1
        
        # Ajouter selon les resources fournies
        if obj.provided_data:
            base_mb += 2
        
        if obj.templates:
            base_mb += 3
        
        return f"~{base_mb} MB"


class ProfessionalTaskDetailSerializer(ProfessionalTaskSerializer):
    """Serializer détaillé avec toutes les données"""
    
    provided_data = serializers.JSONField(read_only=True)
    templates = serializers.JSONField(read_only=True)
    
    class Meta(ProfessionalTaskSerializer.Meta):
        fields = ProfessionalTaskSerializer.Meta.fields + [
            'provided_data', 'templates'
        ]


class TaskGenerateSerializer(serializers.Serializer):
    """Serializer pour générer une tâche avec IA"""
    
    skill = serializers.CharField(required=True, max_length=100)
    difficulty = serializers.ChoiceField(
        choices=ProfessionalTaskSimulation.DIFFICULTY_LEVELS,
        default='intermediate'
    )


class UserTaskAttemptSerializer(serializers.ModelSerializer):
    """Serializer pour les tentatives de tâche"""
    
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_type = serializers.CharField(source='task.task_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_remaining_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTaskAttempt
        fields = [
            'id', 'user', 'task', 'task_title', 'task_type', 'status',
            'status_display', 'time_taken_minutes', 'score', 'detailed_scores',
            'ai_feedback', 'mentor_feedback', 'time_remaining_seconds',
            'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'score', 'detailed_scores', 'ai_feedback',
            'started_at', 'completed_at'
        ]
    
    def get_time_remaining_seconds(self, obj):
        """Temps restant pour la tâche"""
        if obj.status != 'in_progress':
            return 0
        
        from django.utils import timezone
        elapsed = timezone.now() - obj.started_at
        elapsed_minutes = elapsed.total_seconds() / 60
        remaining_minutes = max(0, obj.task.time_limit_minutes - elapsed_minutes)
        
        return int(remaining_minutes * 60)


class TaskSubmitSerializer(serializers.Serializer):
    """Serializer pour soumettre le travail"""
    
    work_data = serializers.JSONField(required=True)
    
    def validate_work_data(self, value):
        """Valide que le travail contient des données"""
        if not value or not isinstance(value, dict):
            raise serializers.ValidationError("Le travail soumis doit contenir des données")
        
        return value