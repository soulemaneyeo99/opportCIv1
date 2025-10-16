# backend/courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonViewSet, UserProgressViewSet,
    QuestionViewSet, UserAnswerViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'progress', UserProgressViewSet, basename='progress')
router.register(r'questions', QuestionViewSet)
router.register(r'answers', UserAnswerViewSet, basename='answers')

urlpatterns = [
    path('', include(router.urls)),
]