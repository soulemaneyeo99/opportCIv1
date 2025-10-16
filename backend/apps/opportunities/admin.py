from django.contrib import admin
from .models import Opportunity, OpportunityCategory, UserOpportunity


@admin.register(OpportunityCategory)
class OpportunityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    ordering = ('name',)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'opportunity_type', 'category', 'organization',
        'creator', 'status', 'featured', 'deadline', 'view_count', 'application_count'
    )
    search_fields = ('title', 'organization', 'description', 'tags')
    list_filter = ('status', 'opportunity_type', 'featured', 'is_remote', 'category')
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'application_count')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('creator', 'category')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ("Informations générales", {
            'fields': ('title', 'slug', 'description', 'category', 'opportunity_type', 'creator')
        }),
        ("Détails", {
            'fields': (
                'organization', 'location', 'is_remote', 'website', 'application_link', 'contact_email',
                'requirements', 'education_level', 'compensation', 'currency', 'tags', 'featured'
            )
        }),
        ("Dates", {
            'fields': ('publication_date', 'deadline', 'created_at', 'updated_at')
        }),
        ("Statut", {
            'fields': ('status', 'view_count', 'application_count')
        }),
    )


@admin.register(UserOpportunity)
class UserOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'opportunity', 'relation_type', 'status', 'created_at'
    )
    search_fields = ('user__email', 'opportunity__title', 'notes')
    list_filter = ('relation_type', 'status')
    autocomplete_fields = ('user', 'opportunity')
    ordering = ('-created_at',)
