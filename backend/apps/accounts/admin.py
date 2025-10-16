from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profil')

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Informations personnelles'), {'fields': (
            'first_name', 'last_name', 'profile_picture', 'bio', 'date_of_birth',
            'phone_number', 'address', 'city', 'country'
        )}),
        (_('Informations académiques'), {'fields': (
            'education_level', 'institution'
        )}),
        (_('Informations d\'organisation'), {'fields': (
            'organization_name', 'organization_type', 'organization_website'
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
            'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
        }),
    )