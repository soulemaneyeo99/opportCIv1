"""
OpportuCI - Opportunities API Serializers
==========================================
"""
from rest_framework import serializers
from django.utils import timezone

from ..models import (
    Opportunity,
    OpportunityCategory,
    OpportunitySource,
    ApplicationTracker
)


class OpportunityCategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories d'opportunités"""

    class Meta:
        model = OpportunityCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active']
        read_only_fields = ['slug']


class OpportunitySourceSerializer(serializers.ModelSerializer):
    """Serializer pour les sources d'opportunités"""

    source_type_display = serializers.CharField(
        source='get_source_type_display',
        read_only=True
    )

    class Meta:
        model = OpportunitySource
        fields = [
            'id', 'name', 'source_type', 'source_type_display',
            'url', 'logo', 'is_active', 'last_scraped_at'
        ]


class OpportunityListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes d'opportunités"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_opportunity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)
    time_left = serializers.SerializerMethodField()
    user_application = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'slug', 'category', 'category_name',
            'opportunity_type', 'type_display', 'organization', 'organization_logo',
            'location', 'is_remote', 'deadline', 'is_expired', 'days_until_deadline',
            'time_left', 'status', 'status_display', 'featured', 'view_count',
            'user_application'
        ]

    def get_time_left(self, obj):
        """Calcule le temps restant de manière lisible"""
        if not obj.deadline:
            return None

        now = timezone.now()
        if obj.deadline < now:
            return "Expirée"

        delta = obj.deadline - now
        days = delta.days

        if days > 30:
            months = days // 30
            return f"{months} mois"
        elif days > 0:
            return f"{days} jours"
        else:
            hours = delta.seconds // 3600
            if hours > 0:
                return f"{hours} heures"
            return f"{(delta.seconds % 3600) // 60} minutes"

    def get_user_application(self, obj):
        """Récupère le statut de candidature de l'utilisateur"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        application = ApplicationTracker.objects.filter(
            user=request.user,
            opportunity=obj
        ).first()

        if application:
            return {
                'status': application.status,
                'ai_match_score': application.ai_match_score,
                'discovered_at': application.discovered_at
            }
        return None


class OpportunityDetailSerializer(OpportunityListSerializer):
    """Serializer complet pour le détail d'une opportunité"""

    category = OpportunityCategorySerializer(read_only=True)
    source = OpportunitySourceSerializer(read_only=True)
    education_level_display = serializers.CharField(
        source='get_education_level_display',
        read_only=True
    )
    matching_data = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'slug', 'description',
            'category', 'opportunity_type', 'type_display',
            'organization', 'organization_logo', 'website',
            'application_link', 'contact_email',
            'location', 'is_remote',
            'publication_date', 'deadline', 'start_date',
            'is_expired', 'days_until_deadline', 'time_left',
            'education_level', 'education_level_display',
            'skills_required', 'experience_years', 'requirements',
            'compensation', 'currency',
            'source', 'external_id', 'status', 'status_display', 'featured',
            'view_count', 'created_at', 'updated_at',
            'user_application', 'matching_data'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'view_count', 'external_id']

    def get_matching_data(self, obj):
        """Retourne les données pour le matching IA"""
        return obj.get_matching_data()


class OpportunityCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une opportunité"""

    class Meta:
        model = Opportunity
        fields = [
            'title', 'description', 'category', 'opportunity_type',
            'organization', 'organization_logo', 'website',
            'application_link', 'contact_email',
            'location', 'is_remote',
            'publication_date', 'deadline', 'start_date',
            'education_level', 'skills_required', 'experience_years', 'requirements',
            'compensation', 'currency',
            'source', 'external_id', 'status', 'featured'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user

        # Auto-publish date
        if validated_data.get('status') == 'published' and not validated_data.get('publication_date'):
            validated_data['publication_date'] = timezone.now()

        return super().create(validated_data)


class ApplicationTrackerSerializer(serializers.ModelSerializer):
    """Serializer pour le suivi des candidatures"""

    opportunity_summary = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ApplicationTracker
        fields = [
            'id', 'opportunity', 'opportunity_summary', 'status', 'status_display',
            'ai_match_score', 'ai_match_reasons',
            'discovered_at', 'saved_at', 'applied_at', 'status_updated_at',
            'notes', 'next_action', 'next_action_date',
            'cv_used', 'cover_letter'
        ]
        read_only_fields = [
            'id', 'discovered_at', 'status_updated_at',
            'ai_match_score', 'ai_match_reasons'
        ]

    def get_opportunity_summary(self, obj):
        """Résumé de l'opportunité"""
        opp = obj.opportunity
        return {
            'id': str(opp.id),
            'title': opp.title,
            'organization': opp.organization,
            'deadline': opp.deadline,
            'is_expired': opp.is_expired
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Serializer pour mettre à jour le statut d'une candidature"""

    status = serializers.ChoiceField(choices=ApplicationTracker.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


# Backward compatibility
UserOpportunitySerializer = ApplicationTrackerSerializer
