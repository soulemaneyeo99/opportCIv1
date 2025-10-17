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
# Ajouter à la fin de la classe GeminiAIService dans gemini_service.py

    def generate_interview_response(
        self,
        conversation: list,
        company_context: dict,
        interview_type: str
    ) -> str:
        """
        Génère la réponse du recruteur IA pendant l'entretien
        
        Args:
            conversation: Historique complet de la conversation
            company_context: Contexte de l'entreprise
            interview_type: Type d'entretien (behavioral, technical, etc.)
        
        Returns:
            Message du recruteur
        """
        # Formater l'historique
        formatted_history = self._format_conversation(conversation)
        
        # Déterminer le nombre de questions posées
        recruiter_messages = [m for m in conversation if m['role'] == 'recruiter']
        question_count = len(recruiter_messages) - 1  # -1 pour le message d'ouverture
        
        # Adapter le prompt selon le type d'entretien
        interview_prompts = {
            'behavioral': "Pose des questions sur l'expérience passée, les soft skills, la gestion de situations",
            'technical': "Pose des questions techniques sur les compétences requises pour le poste",
            'phone': "Garde un ton léger, pose des questions générales de présélection",
            'panel': "Simule plusieurs recruteurs avec des angles différents"
        }
        
        prompt = f"""
        Tu es {company_context['recruiter_name']}, {company_context['recruiter_role']} chez {company_context['company_name']}.
        Tu mènes un entretien {interview_type} pour le poste de {company_context['position']}.
        
        CONTEXTE:
        - Entreprise ivoirienne, culture professionnelle mais bienveillante
        - Durée prévue : ~15 minutes
        - Tu as déjà posé {question_count} questions
        
        INSTRUCTIONS:
        - {interview_prompts.get(interview_type, 'Pose des questions pertinentes')}
        - Reste naturel et professionnel
        - Valorise les bonnes réponses avec des encouragements
        - Si réponse faible, aide avec des indices sans être condescendant
        - Après 5-6 questions, commence à conclure l'entretien
        - Si question_count >= 6, termine l'entretien avec remerciements et prochaines étapes
        
        HISTORIQUE CONVERSATION:
        {formatted_history}
        
        Génère la PROCHAINE question ou remarque du recruteur (1-2 phrases max).
        Si c'est la fin, remercie le candidat et explique la suite.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erreur génération réponse interview: {e}")
            # Fallback
            if question_count >= 6:
                return "Merci beaucoup pour vos réponses. Nous avons terminé cet entretien. Nous reviendrons vers vous dans les prochains jours concernant la suite du processus. Bonne journée !"
            return "Je vois. Pouvez-vous m'en dire un peu plus sur votre motivation pour ce poste ?"
    
    def evaluate_interview(
        self,
        conversation: list,
        opportunity,
        interview_type: str
    ) -> dict:
        """
        Évalue la performance d'entretien avec scoring détaillé
        
        Args:
            conversation: Historique complet
            opportunity: Opportunité visée
            interview_type: Type d'entretien
            
        Returns:
            Dict avec scores, feedback, recommandations
        """
        formatted_history = self._format_conversation(conversation)
        
        prompt = f"""
        Évalue cette simulation d'entretien d'embauche en tant que recruteur professionnel.
        
        POSTE: {opportunity.title} chez {opportunity.organization}
        TYPE: {interview_type}
        SECTEUR: {opportunity.category.name if hasattr(opportunity, 'category') and opportunity.category else 'Général'}
        
        TRANSCRIPT COMPLET:
        {formatted_history}
        
        Fournis une évaluation détaillée en JSON strict (pas de markdown):
        {{
            "overall_score": 75,
            "detailed_scores": {{
                "communication": 80,
                "technical_knowledge": 70,
                "motivation": 85,
                "problem_solving": 65,
                "cultural_fit": 75
            }},
            "strengths": [
                "Point fort 1 avec exemple précis",
                "Point fort 2",
                "Point fort 3"
            ],
            "improvements": [
                "Amélioration 1 avec suggestion concrète",
                "Amélioration 2",
                "Amélioration 3"
            ],
            "standout_moments": [
                "Moment particulièrement bon"
            ],
            "red_flags": [
                "Points d'attention éventuels"
            ],
            "feedback": "Feedback général constructif et encourageant (3-4 phrases)",
            "hiring_recommendation": "hire|maybe|no_hire",
            "recommended_practice": [
                "Exercice pratique 1 pour progresser",
                "Exercice pratique 2"
            ]
        }}
        
        Contexte : Jeune ivoirien en début de carrière, sois juste mais encourageant.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Erreur évaluation interview: {e}")
            # Fallback scores neutres
            return {
                "overall_score": 60,
                "detailed_scores": {
                    "communication": 60,
                    "technical_knowledge": 60,
                    "motivation": 60,
                    "problem_solving": 60,
                    "cultural_fit": 60
                },
                "strengths": ["Participation à la simulation"],
                "improvements": ["Continuer à pratiquer les entretiens"],
                "feedback": "Merci d'avoir complété cette simulation. Continue de t'entraîner !",
                "hiring_recommendation": "maybe",
                "recommended_practice": ["Pratiquer les réponses aux questions comportementales"]
            }
    
    def generate_personalized_help(
        self,
        module,
        user_progress,
        struggles: list
    ) -> str:
        """
        Génère de l'aide personnalisée quand utilisateur a des difficultés
        
        Args:
            module: Module d'apprentissage
            user_progress: Progression utilisateur
            struggles: Liste des points de difficulté détectés
            
        Returns:
            Message d'aide personnalisé
        """
        prompt = f"""
        Un utilisateur rencontre des difficultés sur ce module d'apprentissage.
        
        MODULE: {module.title}
        COMPÉTENCE: {module.skill_taught}
        NIVEAU: {module.get_difficulty_level_display()}
        
        PROGRESSION:
        - Tentatives: {user_progress.attempts}
        - Meilleur score: {user_progress.best_score or 0}%
        - Temps passé: {user_progress.time_spent_minutes} minutes
        
        DIFFICULTÉS DÉTECTÉES: {struggles if struggles else "Scores faibles répétés"}
        
        Génère des conseils personnalisés en français (3-4 paragraphes):
        1. **Diagnostic**: Identifie le problème probable
        2. **Conseils pratiques**: 3 conseils spécifiques et actionnables
        3. **Ressources**: Suggestions de pratique ou révision
        4. **Encouragement**: Message motivant adapté au contexte ivoirien
        
        Ton: Bienveillant, mentor proche, pas condescendant.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erreur génération aide: {e}")
            return "Continue de pratiquer ! Chaque tentative te rapproche du succès. N'hésite pas à revoir les concepts de base avant de réessayer. Tu peux le faire ! 💪"
    
    def generate_learning_path(self, context: dict) -> dict:
        """
        Génère un parcours d'apprentissage optimal avec IA
        
        Args:
            context: Dict avec user_profile, opportunity, skill_gaps
            
        Returns:
            Dict avec modules, durée estimée, conseils
        """
        user_profile = context.get('user_profile', {})
        opportunity = context.get('opportunity', {})
        skill_gaps = context.get('skill_gaps', [])
        
        # Formater les gaps
        gaps_text = "\n".join([
            f"- {gap['skill']}: Gap de {int(gap['gap']*100)}% (Priorité: {gap['priority']})"
            for gap in skill_gaps[:10]  # Top 10
        ])
        
        prompt = f"""
        Crée un parcours d'apprentissage optimal pour ce profil.
        
        UTILISATEUR:
        - Nom: {user_profile.get('name', 'Utilisateur')}
        - Niveau: {user_profile.get('education_level', 'Débutant')}
        - Compétences actuelles: {', '.join(list(user_profile.get('current_skills', {}).keys())[:5])}
        
        OPPORTUNITÉ VISÉE:
        - Poste: {opportunity.get('title', 'Non spécifié')}
        - Entreprise: {opportunity.get('organization', 'Non spécifié')}
        - Type: {opportunity.get('type', 'Non spécifié')}
        
        GAPS DE COMPÉTENCES IDENTIFIÉS:
        {gaps_text}
        
        CONTRAINTES:
        - Parcours max 40 heures (utilisateur a vie active)
        - Priorité aux compétences critiques
        - Contenus adaptés au contexte ivoirien
        - Mix théorie/pratique 30/70
        
        Génère un parcours en JSON strict:
        {{
            "modules": [
                {{
                    "skill": "Python basics",
                    "type": "video",
                    "duration_minutes": 30,
                    "priority": "critical",
                    "title": "Titre attractif en français",
                    "description": "Description courte",
                    "learning_objectives": ["obj1", "obj2", "obj3"],
                    "practical_project": "Projet concret ivoirien"
                }}
            ],
            "estimated_total_hours": 25,
            "recommended_pace": "2h par jour pendant 2 semaines",
            "success_tips": ["tip1", "tip2", "tip3"],
            "milestone_rewards": ["reward1", "reward2"]
        }}
        
        Génère entre 8 et 15 modules selon la complexité.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Erreur génération parcours: {e}")
            # Fallback basique
            return {
                "modules": [
                    {
                        "skill": skill_gaps[0]['skill'] if skill_gaps else "Compétence de base",
                        "type": "video",
                        "duration_minutes": 15,
                        "priority": "high",
                        "title": f"Introduction à {skill_gaps[0]['skill'] if skill_gaps else 'la compétence'}",
                        "description": "Module d'introduction",
                        "learning_objectives": ["Comprendre les bases"],
                        "practical_project": "Exercice pratique"
                    }
                ],
                "estimated_total_hours": 10,
                "recommended_pace": "1h par jour",
                "success_tips": ["Pratique régulière", "Ne pas hésiter à poser des questions"],
                "milestone_rewards": ["Progression constante"]
            }
    
    def _format_conversation(self, conversation: list) -> str:
        """
        Formate l'historique de conversation pour les prompts
        
        Args:
            conversation: Liste de messages {role, message, timestamp}
            
        Returns:
            String formaté
        """
        formatted = []
        for msg in conversation:
            role_label = "Recruteur" if msg['role'] == 'recruiter' else "Candidat"
            formatted.append(f"{role_label}: {msg['message']}")
        
        return "\n".join(formatted)