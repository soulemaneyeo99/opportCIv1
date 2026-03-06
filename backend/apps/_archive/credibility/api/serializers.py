# backend/credibility/serializers.py
from rest_framework import serializers
from ..models import Badge, Achievement, UserBadge, UserAchievement, CredibilityPoints, PointsHistory


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_details = BadgeSerializer(source='badge', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'user', 'badge', 'badge_details', 'awarded_at']
        read_only_fields = ['user', 'awarded_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement_details = AchievementSerializer(source='achievement', read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'achievement_details', 'awarded_at']
        read_only_fields = ['user', 'awarded_at']


class CredibilityPointsSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = CredibilityPoints
        fields = ['id', 'user', 'username', 'points', 'level', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at']


class PointsHistorySerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = PointsHistory
        fields = ['id', 'user', 'username', 'operation', 'points', 'source', 'description', 'created_at']
        read_only_fields = ['user', 'created_at']

