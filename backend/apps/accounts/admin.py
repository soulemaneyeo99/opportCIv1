from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _('Profil')
    fields = (
        'city', 'education_level', 'field_of_study', 'institution',
        'graduation_year', 'skills', 'interests', 'languages',
        'cv', 'linkedin_url', 'portfolio_url', 'bio'
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {'fields': (
            'first_name', 'last_name', 'phone_number', 'profile_picture'
        )}),
        (_('Permissions'), {'fields': (
            'user_type', 'is_active', 'is_verified', 'is_staff', 'is_superuser',
            'groups', 'user_permissions'
        )}),
        (_('Dates importantes'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'education_level', 'field_of_study')
    list_filter = ('city', 'education_level')
    search_fields = ('user__email', 'user__first_name', 'field_of_study')
    raw_id_fields = ('user',)
