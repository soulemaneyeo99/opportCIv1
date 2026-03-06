"""
OpportuCI - Interview Prep API Serializers
===========================================
"""
from rest_framework import serializers
from apps.prep.models import (
    InterviewSimulation,
    ProfessionalTaskSimulation,
    UserTaskAttempt
)


class InterviewSimulationSerializer(serializers.ModelSerializer):
    """Serializer pour les simulations d'entretien"""

    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    opportunity_organization = serializers.CharField(source='opportunity.organization', read_only=True)
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InterviewSimulation
        fields = [
            'id', 'user', 'opportunity', 'opportunity_title', 'opportunity_organization',
            'interview_type', 'interview_type_display', 'difficulty', 'difficulty_display',
            'duration_minutes', 'company_context', 'status', 'status_display',
            'overall_score', 'detailed_scores', 'ai_feedback', 'strengths', 'improvements',
            'recommended_practice', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'company_context', 'overall_score', 'detailed_scores',
            'ai_feedback', 'strengths', 'improvements', 'recommended_practice',
            'created_at', 'started_at', 'completed_at'
        ]


class InterviewSimulationDetailSerializer(InterviewSimulationSerializer):
    """Serializer détaillé avec conversation complète"""

    conversation = serializers.JSONField(read_only=True)

    class Meta(InterviewSimulationSerializer.Meta):
        fields = InterviewSimulationSerializer.Meta.fields + ['conversation']


class InterviewSimulationCreateSerializer(serializers.Serializer):
    """Serializer pour créer une simulation"""

    opportunity_id = serializers.UUIDField(required=True)
    interview_type = serializers.ChoiceField(
        choices=InterviewSimulation.InterviewType.choices,
        default='behavioral'
    )
    difficulty = serializers.ChoiceField(
        choices=InterviewSimulation.Difficulty.choices,
        default='medium'
    )

    def validate_opportunity_id(self, value):
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

    class Meta:
        model = ProfessionalTaskSimulation
        fields = [
            'id', 'title', 'task_type', 'task_type_display', 'description',
            'scenario', 'company_context', 'objectives', 'deliverables',
            'evaluation_criteria', 'time_limit_minutes', 'difficulty',
            'difficulty_display', 'points_reward', 'total_attempts',
            'average_score', 'average_completion_time', 'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_attempts', 'average_score', 'average_completion_time', 'created_at'
        ]


class ProfessionalTaskDetailSerializer(ProfessionalTaskSerializer):
    """Serializer détaillé avec toutes les données"""

    provided_data = serializers.JSONField(read_only=True)
    templates = serializers.JSONField(read_only=True)

    class Meta(ProfessionalTaskSerializer.Meta):
        fields = ProfessionalTaskSerializer.Meta.fields + ['provided_data', 'templates']


class UserTaskAttemptSerializer(serializers.ModelSerializer):
    """Serializer pour les tentatives de tâche"""

    task_title = serializers.CharField(source='task.title', read_only=True)
    task_type = serializers.CharField(source='task.task_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserTaskAttempt
        fields = [
            'id', 'user', 'task', 'task_title', 'task_type', 'status',
            'status_display', 'time_taken_minutes', 'score', 'detailed_scores',
            'ai_feedback', 'mentor_feedback', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'score', 'detailed_scores', 'ai_feedback',
            'started_at', 'completed_at'
        ]


class TaskSubmitSerializer(serializers.Serializer):
    """Serializer pour soumettre le travail"""

    work_data = serializers.JSONField(required=True)

    def validate_work_data(self, value):
        if not value or not isinstance(value, dict):
            raise serializers.ValidationError("Le travail soumis doit contenir des données")
        return value


class TaskGenerateSerializer(serializers.Serializer):
    """Serializer pour générer une tâche personnalisée avec IA"""

    skill = serializers.CharField(required=True, min_length=2, max_length=100)
    difficulty = serializers.ChoiceField(
        choices=[
            ('beginner', 'Débutant'),
            ('intermediate', 'Intermédiaire'),
            ('advanced', 'Avancé')
        ],
        default='intermediate'
    )
