# backend/credibility/admin.py
from django.contrib import admin
from .models import (
    Badge, Achievement, UserBadge, UserAchievement,
    CredibilityPoints, PointsHistory
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'points_required', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'points', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge__category',)
    search_fields = ('user__username', 'badge__name')
    autocomplete_fields = ('user', 'badge')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'awarded_at')
    list_filter = ('achievement__category',)
    search_fields = ('user__username', 'achievement__name')
    autocomplete_fields = ('user', 'achievement')


@admin.register(CredibilityPoints)
class CredibilityPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'level', 'updated_at')
    search_fields = ('user__username',)
    ordering = ('-points',)
    autocomplete_fields = ('user',)


@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'operation', 'points', 'source', 'description', 'created_at')
    list_filter = ('operation', 'source')
    search_fields = ('user__username', 'description')
    ordering = ('-created_at',)
    autocomplete_fields = ('user',)
