from django.contrib import admin
from .models import Category, Formation, Enrollment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'instructor', 'start_date', 'end_date',
        'status', 'is_online', 'is_free', 'price', 'current_participants_count', 'max_participants'
    )
    list_filter = ('status', 'is_online', 'is_free', 'category')
    search_fields = ('title', 'instructor', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'current_participants_count')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    @admin.display(description='Participants')
    def current_participants_count(self, obj):
        return obj.current_participants_count


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'formation', 'status', 'enrollment_date', 'completion_percentage',
        'certificate_issued', 'rating'
    )
    list_filter = ('status', 'certificate_issued', 'rating')
    search_fields = ('user__username', 'formation__title', 'feedback')
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
