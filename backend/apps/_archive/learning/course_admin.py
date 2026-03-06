from django.contrib import admin
from .models import Course, Lesson, UserProgress, Question, Answer, UserAnswer

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'formation', 'instructor', 'difficulty', 'order', 'is_published', 'created_at')
    list_filter = ('formation', 'difficulty', 'is_published')
    search_fields = ('title', 'description', 'instructor')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('formation', 'order')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'type', 'duration_minutes', 'order', 'is_published')
    list_filter = ('type', 'is_published')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('course', 'order')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completion_date', 'last_position_seconds')
    list_filter = ('completed',)
    search_fields = ('user__email', 'lesson__title')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'difficulty', 'points')
    list_filter = ('difficulty',)
    search_fields = ('text',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text',)

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'answer', 'is_correct', 'created_at')
    search_fields = ('user__email', 'question__text', 'answer__text')
