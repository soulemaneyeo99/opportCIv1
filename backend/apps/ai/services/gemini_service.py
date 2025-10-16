# backend/ai_services/gemini_service.py
import google.generativeai as genai
from django.conf import settings
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service d'IA utilisant l'API Gemini gratuite pour OpportuCI"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def get_opportunity_recommendations(self, user_profile: Dict, opportunities: List[Dict], limit: int = 5) -> List[Dict]:
        """
        Recommande des opportunités basées sur le profil utilisateur
        Utilise Gemini pour analyser la compatibilité
        """
        try:
            # Préparer le prompt avec les données utilisateur
            user_context = self._format_user_profile(user_profile)
            opportunities_context = self._format_opportunities(opportunities[:20])  # Limite pour éviter de dépasser les tokens
            
            prompt = f"""
            En tant qu'expert en orientation professionnelle pour jeunes ivoiriens, analysez ce profil utilisateur et recommandez les {limit} meilleures opportunités parmi celles disponibles.

            PROFIL UTILISATEUR:
            {user_context}

            OPPORTUNITÉS DISPONIBLES:
            {opportunities_context}

            Retournez uniquement un JSON avec cette structure (pas de texte avant/après):
            {{
                "recommendations": [
                    {{
                        "opportunity_id": "id",
                        "match_score": 0.85,
                        "match_reason": "Raison de la compatibilité en français",
                        "key_advantages": ["avantage1", "avantage2"]
                    }}
                ]
            }}
            
            Critères de matching:
            - Compétences requises vs acquises
            - Niveau d'éducation
            - Centres d'intérêt
            - Localisation
            - Opportunités de développement
            """
            
            response = self.model.generate_content(prompt)
            
            # Parser la réponse JSON
            try:
                result = json.loads(response.text.strip())
                return result.get('recommendations', [])
            except json.JSONDecodeError:
                logger.error(f"Erreur parsing JSON: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur Gemini recommendations: {str(e)}")
            return []
    
    def generate_career_advice(self, user_profile: Dict, career_goals: str = "") -> Dict:
        """Génère des conseils de carrière personnalisés"""
        try:
            user_context = self._format_user_profile(user_profile)
            
            prompt = f"""
            En tant que conseiller en carrière spécialisé dans le marché du travail ivoirien et africain, analysez ce profil et donnez des conseils personnalisés.

            PROFIL:
            {user_context}
            
            OBJECTIFS DE CARRIÈRE: {career_goals or "Non spécifiés"}

            Retournez uniquement un JSON avec cette structure:
            {{
                "career_assessment": {{
                    "strengths": ["force1", "force2", "force3"],
                    "areas_to_improve": ["amélioration1", "amélioration2"],
                    "market_opportunities": ["opportunité1", "opportunité2"],
                    "recommended_skills": ["compétence1", "compétence2", "compétence3"],
                    "next_steps": ["étape1", "étape2", "étape3"],
                    "salary_estimation": "Estimation en FCFA pour la Côte d'Ivoire",
                    "career_path_suggestions": ["voie1", "voie2"]
                }}
            }}
            
            Contexte important: Marché du travail ivoirien/africain, secteurs en croissance (tech, agribusiness, finance), défis locaux.
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                result = json.loads(response.text.strip())
                return result.get('career_assessment', {})
            except json.JSONDecodeError:
                logger.error(f"Erreur parsing career advice: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Erreur Gemini career advice: {str(e)}")
            return {}
    
    def analyze_skill_gaps(self, user_skills: List[str], target_position: str) -> Dict:
        """Analyse les gaps de compétences pour un poste cible"""
        try:
            prompt = f"""
            Analysez les compétences actuelles d'un utilisateur par rapport à un poste cible sur le marché ivoirien.

            COMPÉTENCES ACTUELLES: {', '.join(user_skills)}
            POSTE VISÉ: {target_position}

            Retournez uniquement un JSON:
            {{
                "skill_analysis": {{
                    "matching_skills": ["compétence correspondante1", "compétence correspondante2"],
                    "missing_critical_skills": ["compétence critique manquante1", "compétence critique manquante2"],
                    "nice_to_have_skills": ["compétence bonus1", "compétence bonus2"],
                    "learning_priority": ["priorité1", "priorité2", "priorité3"],
                    "estimated_learning_time": "X mois",
                    "recommended_resources": [
                        {{"skill": "compétence", "resource": "ressource recommandée", "type": "cours/certification/pratique"}}
                    ]
                }}
            }}
            
            Contexte: Marché du travail ivoirien, ressources disponibles localement.
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                result = json.loads(response.text.strip())
                return result.get('skill_analysis', {})
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            logger.error(f"Erreur skill gaps analysis: {str(e)}")
            return {}
    
    def generate_interview_prep(self, opportunity: Dict, user_profile: Dict) -> Dict:
        """Génère une préparation d'entretien personnalisée"""
        try:
            user_context = self._format_user_profile(user_profile)
            
            prompt = f"""
            Préparez un guide d'entretien personnalisé pour cette opportunité.

            OPPORTUNITÉ:
            - Titre: {opportunity.get('title', '')}
            - Organisation: {opportunity.get('organization', '')}
            - Description: {opportunity.get('description', '')[:500]}
            - Secteur: {opportunity.get('category', '')}

            PROFIL CANDIDAT:
            {user_context}

            Retournez uniquement un JSON:
            {{
                "interview_prep": {{
                    "likely_questions": [
                        {{"question": "Question probable", "suggested_answer_points": ["point1", "point2"], "why_this_question": "Explication"}}
                    ],
                    "key_strengths_to_highlight": ["force à mettre en avant1", "force à mettre en avant2"],
                    "potential_concerns_to_address": ["préoccupation potentielle1"],
                    "questions_to_ask_interviewer": ["question1", "question2", "question3"],
                    "company_research_points": ["point recherche1", "point recherche2"],
                    "dress_code_suggestion": "Code vestimentaire recommandé",
                    "cultural_tips": "Conseils culturels pour le contexte ivoirien/africain"
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                result = json.loads(response.text.strip())
                return result.get('interview_prep', {})
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            logger.error(f"Erreur interview prep: {str(e)}")
            return {}
    
    def _format_user_profile(self, profile: Dict) -> str:
        """Formate le profil utilisateur pour les prompts"""
        return f"""
        - Nom: {profile.get('name', 'Non spécifié')}
        - Niveau d'éducation: {profile.get('education_level', 'Non spécifié')}
        - Institution: {profile.get('institution', 'Non spécifié')}
        - Compétences: {', '.join(profile.get('skills', []))}
        - Centres d'intérêt: {', '.join(profile.get('interests', []))}
        - Localisation: {profile.get('location', 'Côte d\'Ivoire')}
        - Expérience: {profile.get('experience', 'Débutant')}
        - Objectifs: {profile.get('career_goals', 'En définition')}
        """
    
    def _format_opportunities(self, opportunities: List[Dict]) -> str:
        """Formate la liste d'opportunités pour les prompts"""
        formatted = []
        for i, opp in enumerate(opportunities, 1):
            formatted.append(f"""
            {i}. ID: {opp.get('id')} | Titre: {opp.get('title', '')} | 
            Organisation: {opp.get('organization', '')} | 
            Catégorie: {opp.get('category', '')} | 
            Lieu: {opp.get('location', '')} | 
            Niveau: {opp.get('education_level', 'Tous niveaux')} | 
            Description: {opp.get('description', '')[:200]}...
            """)
        return '\n'.join(formatted)
