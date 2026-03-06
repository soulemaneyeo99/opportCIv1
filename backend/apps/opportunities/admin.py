"""
OpportuCI - Opportunities Admin
===============================
"""
from django.contrib import admin
from .models import Opportunity, OpportunityCategory, OpportunitySource, ApplicationTracker


@admin.register(OpportunityCategory)
class OpportunityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    ordering = ('name',)


@admin.register(OpportunitySource)
class OpportunitySourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'url', 'is_active', 'last_scraped_at')
    search_fields = ('name', 'url')
    list_filter = ('source_type', 'is_active')
    ordering = ('name',)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'opportunity_type', 'category', 'organization',
        'status', 'featured', 'deadline', 'view_count', 'get_application_count'
    )
    search_fields = ('title', 'organization', 'description')
    list_filter = ('status', 'opportunity_type', 'featured', 'is_remote', 'category', 'source')
    readonly_fields = ('created_at', 'updated_at', 'view_count')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('category',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ("Informations générales", {
            'fields': ('title', 'slug', 'description', 'category', 'opportunity_type')
        }),
        ("Organisation", {
            'fields': (
                'organization', 'organization_logo', 'website',
                'application_link', 'contact_email'
            )
        }),
        ("Localisation", {
            'fields': ('location', 'is_remote')
        }),
        ("Exigences", {
            'fields': (
                'education_level', 'skills_required', 'experience_years', 'requirements'
            )
        }),
        ("Financier", {
            'fields': ('compensation', 'currency')
        }),
        ("Dates", {
            'fields': ('publication_date', 'deadline', 'start_date', 'created_at', 'updated_at')
        }),
        ("Source & Statut", {
            'fields': ('source', 'external_id', 'status', 'featured', 'view_count')
        }),
    )

    def get_application_count(self, obj):
        return obj.applications.count()
    get_application_count.short_description = 'Candidatures'


@admin.register(ApplicationTracker)
class ApplicationTrackerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'opportunity', 'status', 'ai_match_score', 'discovered_at'
    )
    search_fields = ('user__email', 'opportunity__title', 'notes')
    list_filter = ('status',)
    autocomplete_fields = ('user', 'opportunity')
    ordering = ('-discovered_at',)
    readonly_fields = ('discovered_at', 'status_updated_at', 'ai_match_score', 'ai_match_reasons')

    fieldsets = (
        ("Relation", {
            'fields': ('user', 'opportunity', 'status')
        }),
        ("IA Matching", {
            'fields': ('ai_match_score', 'ai_match_reasons'),
            'classes': ('collapse',)
        }),
        ("Suivi", {
            'fields': ('notes', 'next_action', 'next_action_date')
        }),
        ("Documents", {
            'fields': ('cv_used', 'cover_letter'),
            'classes': ('collapse',)
        }),
        ("Dates", {
            'fields': ('discovered_at', 'saved_at', 'applied_at', 'status_updated_at')
        }),
    )
