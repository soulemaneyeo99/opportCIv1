# opportunities/serializers.py
from rest_framework import serializers
from ..models import Opportunity, OpportunityCategory, UserOpportunity
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class OpportunityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityCategory
        fields = '__all__'

class OpportunityListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    creator_name = serializers.ReadOnlyField(source='creator.get_full_name')
    is_expired = serializers.BooleanField(read_only=True)
    time_left = serializers.SerializerMethodField()
    user_relation = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = ('id', 'title', 'slug', 'category', 'category_name', 'opportunity_type',
                 'deadline', 'location', 'is_remote', 'organization', 'featured',
                 'status', 'creator_name', 'is_expired', 'time_left', 'user_relation')
    
    def get_time_left(self, obj):
        """Calculer le temps restant avant la date limite"""
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
            else:
                minutes = (delta.seconds % 3600) // 60
                return f"{minutes} minutes"
    
    def get_user_relation(self, obj):
        """Récupérer la relation de l'utilisateur avec cette opportunité"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
            
        user_relations = UserOpportunity.objects.filter(
            user=request.user,
            opportunity=obj
        ).values_list('relation_type', flat=True)
        
        return list(user_relations) if user_relations else None

class OpportunityDetailSerializer(OpportunityListSerializer):
    category = OpportunityCategorySerializer(read_only=True)
    
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at', 
                          'view_count', 'application_count', 'creator')

class OpportunityCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        exclude = ('id', 'slug', 'created_at', 'updated_at', 'creator', 
                  'view_count', 'application_count')
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['creator'] = request.user
        
        # Si le statut est "published", définir la date de publication
        if validated_data.get('status') == 'published' and not validated_data.get('publication_date'):
            validated_data['publication_date'] = timezone.now()
            
        return super().create(validated_data)

class UserOpportunitySerializer(serializers.ModelSerializer):
    opportunity_details = OpportunityListSerializer(source='opportunity', read_only=True)
    
    class Meta:
        model = UserOpportunity
        fields = ('id', 'opportunity', 'opportunity_details', 'relation_type', 
                 'created_at', 'updated_at', 'notes', 'status')
        read_only_fields = ('id', 'created_at', 'updated_at', 'user')
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
