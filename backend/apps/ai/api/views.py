# backend/ai_services/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.opportunities.models import Opportunity
from .gemini_service import GeminiAIService
import logging

logger = logging.getLogger(__name__)

class AIRecommendationsView(APIView):
    """API pour les recommandations IA via Gemini"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Récupérer le profil utilisateur
            user_profile = {
                'name': user.get_full_name(),
                'education_level': getattr(user, 'education_level', ''),
                'institution': getattr(user, 'institution', ''),
                'skills': user.profile.get_skills_list() if hasattr(user, 'profile') else [],
                'interests': user.profile.get_interests_list() if hasattr(user, 'profile') else [],
                'location': f"{user.city}, {user.country}" if user.city else user.country,
                'experience': 'Débutant',  # À adapter selon votre modèle
            }
            
            # Récupérer les opportunités disponibles
            opportunities = list(
                Opportunity.objects.filter(status='published')
                .exclude(user_relations__user=user, user_relations__relation_type='applied')
                .values('id', 'title', 'organization', 'category', 'location', 'description', 'education_level')[:50]
            )
            
            if not opportunities:
                return Response({
                    'recommendations': [],
                    'message': 'Aucune opportunité disponible pour le moment.'
                })
            
            # Utiliser Gemini pour les recommandations
            gemini_service = GeminiAIService()
            recommendations = gemini_service.get_opportunity_recommendations(
                user_profile=user_profile,
                opportunities=opportunities,
                limit=10
            )
            
            # Enrichir avec les données complètes des opportunités
            enriched_recommendations = []
            for rec in recommendations:
                try:
                    opp = Opportunity.objects.get(id=rec['opportunity_id'])
                    enriched_recommendations.append({
                        'id': opp.id,
                        'title': opp.title,
                        'organization': opp.organization,
                        'category': opp.category.name if opp.category else 'Autre',
                        'location': opp.location,
                        'deadline': opp.deadline,
                        'slug': opp.slug,
                        'match_score': rec.get('match_score', 0.5),
                        'match_reason': rec.get('match_reason', 'Profil compatible'),
                        'key_advantages': rec.get('key_advantages', [])
                    })
                except Opportunity.DoesNotExist:
                    continue
            
            return Response({
                'recommendations': enriched_recommendations,
                'total': len(enriched_recommendations)
            })
            
        except Exception as e:
            logger.error(f"Erreur AI recommendations: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la génération des recommandations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AICareerAdviceView(APIView):
    """API pour les conseils de carrière IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            career_goals = request.data.get('career_goals', '')
            
            user_profile = {
                'name': user.get_full_name(),
                'education_level': getattr(user, 'education_level', ''),
                'institution': getattr(user, 'institution', ''),
                'skills': user.profile.get_skills_list() if hasattr(user, 'profile') else [],
                'interests': user.profile.get_interests_list() if hasattr(user, 'profile') else [],
                'location': f"{user.city}, {user.country}" if user.city else user.country,
            }
            
            gemini_service = GeminiAIService()
            advice = gemini_service.generate_career_advice(user_profile, career_goals)
            
            if not advice:
                return Response(
                    {'error': 'Impossible de générer des conseils pour le moment'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({'career_advice': advice})
            
        except Exception as e:
            logger.error(f"Erreur career advice: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la génération des conseils'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AIInterviewPrepView(APIView):
    """API pour la préparation d'entretien IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            opportunity_id = request.data.get('opportunity_id')
            if not opportunity_id:
                return Response(
                    {'error': 'opportunity_id requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            opportunity = get_object_or_404(Opportunity, id=opportunity_id)
            user = request.user
            
            # Préparer les données
            opportunity_data = {
                'title': opportunity.title,
                'organization': opportunity.organization,
                'description': opportunity.description,
                'category': opportunity.category.name if opportunity.category else 'Autre'
            }
            
            user_profile = {
                'name': user.get_full_name(),
                'education_level': getattr(user, 'education_level', ''),
                'skills': user.profile.get_skills_list() if hasattr(user, 'profile') else [],
                'experience': 'Débutant'  # À adapter
            }
            
            gemini_service = GeminiAIService()
            prep = gemini_service.generate_interview_prep(opportunity_data, user_profile)
            
            return Response({'interview_prep': prep})
            
        except Exception as e:
            logger.error(f"Erreur interview prep: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la préparation d\'entretien'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )