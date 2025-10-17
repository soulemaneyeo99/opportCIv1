"""
OpportuCI - Simulations Admin
==============================
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from apps.simulations.models import (
    InterviewSimulation,
    ProfessionalTaskSimulation,
    UserTaskAttempt
)


@admin.register(InterviewSimulation)
class InterviewSimulationAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'opportunity_short',
        'interview_type_badge',
        'difficulty_badge',
        'status_badge',
        'score_display',
        'created_at'
    )
    list_filter = ('status', 'interview_type', 'difficulty', 'created_at')
    search_fields = ('user__username', 'user__email', 'opportunity__title')
    readonly_fields = (
        'id', 'user', 'opportunity', 'company_context', 'conversation',
        'overall_score', 'detailed_scores', 'ai_feedback',
        'strengths', 'improvements', 'recommended_practice',
        'created_at', 'started_at', 'completed_at'
    )
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'user', 'opportunity')
        }),
        ('Configuration', {
            'fields': ('interview_type', 'difficulty', 'duration_minutes', 'company_context')
        }),
        ('État', {
            'fields': ('status', 'conversation')
        }),
        ('Évaluation', {
            'fields': (
                'overall_score', 'detailed_scores', 'ai_feedback',
                'strengths', 'improvements', 'recommended_practice'
            )
        }),
        ('Dates', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def opportunity_short(self, obj):
        return f"{obj.opportunity.title[:40]}..."
    opportunity_short.short_description = 'Opportunité'
    
    def interview_type_badge(self, obj):
        colors = {
            'phone': 'blue',
            'video': 'purple',
            'technical': 'orange',
            'behavioral': 'green',
            'panel': 'red'
        }
        color = colors.get(obj.interview_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_interview_type_display()
        )
    interview_type_badge.short_description = 'Type'
    
    def difficulty_badge(self, obj):
        colors = {'easy': 'green', 'medium': 'orange', 'hard': 'red'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.difficulty, 'gray'), obj.get_difficulty_display()
        )
    difficulty_badge.short_description = 'Difficulté'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'abandoned': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def score_display(self, obj):
        if obj.overall_score is None:
            return '-'
        
        color = 'green' if obj.overall_score >= 70 else 'orange' if obj.overall_score >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.overall_score
        )
    score_display.short_description = 'Score'


@admin.register(ProfessionalTaskSimulation)
class ProfessionalTaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'task_type_badge',
        'difficulty_badge',
        'time_limit_display',
        'stats_display',
        'is_active',
        'created_at'
    )
    list_filter = ('task_type', 'difficulty', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'scenario')
    readonly_fields = (
        'total_attempts', 'average_score', 'average_completion_time', 'created_at'
    )
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'task_type', 'description', 'difficulty')
        }),
        ('Scénario', {
            'fields': ('scenario', 'company_context')
        }),
        ('Objectifs', {
            'fields': ('objectives', 'deliverables')
        }),
        ('Ressources', {
            'fields': ('provided_data', 'templates')
        }),
        ('Évaluation', {
            'fields': ('evaluation_criteria', 'time_limit_minutes', 'points_reward')
        }),
        ('Statistiques', {
            'fields': ('total_attempts', 'average_score', 'average_completion_time')
        }),
        ('Gestion', {
            'fields': ('is_active', 'created_by', 'created_at')
        }),
    )
    
    def task_type_badge(self, obj):
        return format_html(
            '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.get_task_type_display()
        )
    task_type_badge.short_description = 'Type'
    
    def difficulty_badge(self, obj):
        colors = {'beginner': 'green', 'intermediate': 'orange', 'advanced': 'red'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.difficulty, 'gray'), obj.get_difficulty_display()
        )
    difficulty_badge.short_description = 'Niveau'
    
    def time_limit_display(self, obj):
        return f"{obj.time_limit_minutes} min"
    time_limit_display.short_description = 'Temps'
    
    def stats_display(self, obj):
        return format_html(
            '👥 {} | ⭐ {:.1f}% | ⏱️ {}min',
            obj.total_attempts, obj.average_score, obj.average_completion_time
        )
    stats_display.short_description = 'Statistiques'


@admin.register(UserTaskAttempt)
class UserTaskAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'task_title_short',
        'status_badge',
        'score_display',
        'time_display',
        'started_at'
    )
    list_filter = ('status', 'task__task_type', 'started_at')
    search_fields = ('user__username', 'task__title')
    readonly_fields = (
        'id', 'user', 'task', 'submitted_work', 'score', 'detailed_scores',
        'ai_feedback', 'started_at', 'completed_at'
    )
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'user', 'task', 'status')
        }),
        ('Travail soumis', {
            'fields': ('submitted_work', 'submission_time', 'time_taken_minutes')
        }),
        ('Évaluation', {
            'fields': ('score', 'detailed_scores', 'ai_feedback', 'mentor_feedback')
        }),
        ('Dates', {
            'fields': ('started_at', 'completed_at')
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def task_title_short(self, obj):
        return f"{obj.task.title[:40]}..."
    task_title_short.short_description = 'Tâche'
    
    def status_badge(self, obj):
        colors = {
            'in_progress': 'blue',
            'submitted': 'orange',
            'evaluated': 'green',
            'needs_revision': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def score_display(self, obj):
        if obj.score is None:
            return '-'
        
        color = 'green' if obj.score >= 70 else 'orange' if obj.score >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.score
        )
    score_display.short_description = 'Score'
    
    def time_display(self, obj):
        if obj.time_taken_minutes:
            status = '✅' if obj.time_taken_minutes <= obj.task.time_limit_minutes else '⏰'
            return f"{status} {obj.time_taken_minutes} / {obj.task.time_limit_minutes} min"
        return '-'
    time_display.short_description = 'Temps'