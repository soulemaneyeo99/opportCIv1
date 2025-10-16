# backend/ai_services/urls.py
from django.urls import path
from .views import AIRecommendationsView, AICareerAdviceView, AIInterviewPrepView

urlpatterns = [
    path('recommendations/', AIRecommendationsView.as_view(), name='ai-recommendations'),
    path('career-advice/', AICareerAdviceView.as_view(), name='ai-career-advice'),
    path('interview-prep/', AIInterviewPrepView.as_view(), name='ai-interview-prep'),
]