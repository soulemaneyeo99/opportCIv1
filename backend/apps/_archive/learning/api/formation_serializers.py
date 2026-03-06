# backend/formations/serializers.py
from rest_framework import serializers
from .models import Category, Formation, Enrollment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class FormationListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    is_full = serializers.ReadOnlyField()
    current_participants_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Formation
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_name',
            'instructor', 'image', 'start_date', 'end_date', 'location',
            'is_online', 'is_free', 'price', 'status', 'is_full',
            'max_participants', 'current_participants_count'
        ]


class FormationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    is_full = serializers.ReadOnlyField()
    current_participants_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Formation
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    formation_title = serializers.ReadOnlyField(source='formation.title')
    formation_start_date = serializers.ReadOnlyField(source='formation.start_date')
    formation_end_date = serializers.ReadOnlyField(source='formation.end_date')
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'username', 'formation', 'formation_title', 
            'formation_start_date', 'formation_end_date', 'status', 
            'enrollment_date', 'completion_percentage', 'certificate_issued',
            'feedback', 'rating'
        ]
        read_only_fields = ['user', 'enrollment_date', 'certificate_issued']
    
    def create(self, validated_data):
        # Automatiquement attribuer l'utilisateur actuel
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

