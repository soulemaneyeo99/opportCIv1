"""
OpportuCI - Learning API Serializers
=====================================
Sérialiseurs pour l'API Learning
"""
from rest_framework import serializers
from apps.learning.models import (
    PersonalizedLearningJourney,
    MicroLearningModule ,
    UserModuleProgress,
    JourneyModule
)


class MicroModuleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les micro-modules"""
    
    is_completed = serializers.SerializerMethodField()
    user_score = serializers.SerializerMethodField()
    
    class Meta:
        model = MicroLearningModule
        fields = [
            'id', 'title', 'slug', 'skill_taught', 'description',
            'content_type', 'duration_minutes', 'difficulty_level',
            'points_reward', 'estimated_data_mb', 'local_examples',
            'total_completions', 'average_score', 'success_rate',
            'is_completed', 'user_score'
        ]
    
    def get_is_completed(self, obj):
        """Vérifie si l'utilisateur a complété ce module"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return UserModuleProgress.objects.filter(
            user=request.user,
            module=obj,
            status='completed'
        ).exists()
    
    def get_user_score(self, obj):
        """Récupère le meilleur score de l'utilisateur"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        progress = UserModuleProgress.objects.filter(
            user=request.user,
            module=obj
        ).first()
        
        return progress.best_score if progress else None


class UserProgressSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la progression utilisateur"""
    
    module = MicroModuleSerializer(read_only=True)
    
    class Meta:
        model = UserModuleProgress
        fields = [
            'id', 'module', 'status', 'progress_percentage',
            'attempts', 'best_score', 'last_score', 'time_spent_minutes',
            'started_at', 'last_accessed', 'completed_at'
        ]


class JourneyModuleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les modules d'un parcours"""
    
    module = MicroModuleSerializer(read_only=True)
    
    class Meta:
        model = JourneyModule
        fields = [
            'id', 'module', 'order', 'priority', 'is_mandatory',
            'started', 'completed', 'time_spent_minutes', 'best_score',
            'started_at', 'completed_at'
        ]


class LearningJourneySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les parcours d'apprentissage"""
    
    opportunity_title = serializers.CharField(source='target_opportunity.title', read_only=True)
    opportunity_organization = serializers.CharField(source='target_opportunity.organization', read_only=True)
    modules = JourneyModuleSerializer(source='journeymodule_set', many=True, read_only=True)
    completion_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PersonalizedLearningJourney
        fields = [
            'id', 'target_opportunity', 'opportunity_title', 'opportunity_organization',
            'status', 'skill_gaps', 'total_estimated_hours', 'hours_completed',
            'progress_percentage', 'success_probability', 'estimated_completion_date',
            'modules', 'completion_status', 'created_at', 'started_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_completion_status(self, obj):
        """Statut de complétion détaillé"""
        total_modules = obj.learning_modules.count()
        completed_modules = JourneyModule.objects.filter(
            journey=obj,
            completed=True
        ).count()
        
        return {
            'total_modules': total_modules,
            'completed_modules': completed_modules,
            'remaining_modules': total_modules - completed_modules,
            'is_complete': obj.status == 'completed'
        }


class JourneyCreateSerializer(serializers.Serializer):
    """Sérialiseur pour créer un nouveau parcours"""
    
    opportunity_id = serializers.IntegerField(required=True)
    
    def validate_opportunity_id(self, value):
        """Valide que l'opportunité existe"""
        from apps.opportunities.models import Opportunity
        
        if not Opportunity.objects.filter(id=value, status='published').exists():
            raise serializers.ValidationError("Opportunité introuvable ou non publiée")
        
        return value