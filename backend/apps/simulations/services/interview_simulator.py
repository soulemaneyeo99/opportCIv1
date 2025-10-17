"""
OpportuCI - Interview Simulator Service
========================================
Gestion des simulations d'entretien avec IA
"""
from typing import Dict, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.simulations.models import InterviewSimulation
from apps.opportunities.models import Opportunity
from apps.ai.services.gemini_service import GeminiAIService
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class InterviewSimulatorService:
    """Service pour créer et gérer les simulations d'entretien"""
    
    def __init__(self):
        self.gemini = GeminiService()
    
    def create_simulation(
        self,
        user: User,
        opportunity: Opportunity,
        interview_type: str = 'behavioral',
        difficulty: str = 'medium'
    ) -> Optional[InterviewSimulation]:
        """
        Crée une nouvelle simulation d'entretien
        """
        try:
            # Générer contexte entreprise avec IA
            company_context = self._generate_company_context(opportunity)
            
            simulation = InterviewSimulation.objects.create(
                user=user,
                opportunity=opportunity,
                interview_type=interview_type,
                difficulty=difficulty,
                company_context=company_context
            )
            
            return simulation
            
        except Exception as e:
            logger.error(f"Erreur création simulation: {e}", exc_info=True)
            return None
    
    def start_simulation(self, simulation: InterviewSimulation) -> str:
        """
        Démarre la simulation et retourne le premier message du recruteur IA
        """
        simulation.status = 'in_progress'
        simulation.started_at = timezone.now()
        simulation.save()
        
        # Premier message du recruteur
        first_message = self._generate_opening_message(simulation)
        
        simulation.conversation.append({
            'role': 'recruiter',
            'message': first_message,
            'timestamp': 0
        })
        simulation.save()
        
        return first_message
    
    def process_user_response(
        self,
        simulation: InterviewSimulation,
        user_message: str
    ) -> str:
        """
        Traite la réponse utilisateur et génère la question suivante
        """
        # Enregistrer message utilisateur
        current_time = self._get_elapsed_seconds(simulation)
        
        simulation.conversation.append({
            'role': 'user',
            'message': user_message,
            'timestamp': current_time
        })
        
        # Générer réponse recruteur avec IA
        recruiter_response = self.gemini.generate_interview_response(
            conversation=simulation.conversation,
            company_context=simulation.company_context,
            interview_type=simulation.interview_type
        )
        
        simulation.conversation.append({
            'role': 'recruiter',
            'message': recruiter_response,
            'timestamp': current_time + 5
        })
        
        # Vérifier si fin d'entretien
        if self._should_end_interview(simulation):
            self.finalize_interview(simulation)
        
        simulation.save()
        
        return recruiter_response
    
    def finalize_interview(self, simulation: InterviewSimulation):
        """
        Finalise l'entretien et génère l'évaluation
        """
        simulation.status = 'completed'
        simulation.completed_at = timezone.now()
        
        # Évaluation par IA
        evaluation = self.gemini.evaluate_interview(
            conversation=simulation.conversation,
            opportunity=simulation.opportunity,
            interview_type=simulation.interview_type
        )
        
        simulation.overall_score = evaluation.get('overall_score', 50)
        simulation.detailed_scores = evaluation.get('detailed_scores', {})
        simulation.ai_feedback = evaluation.get('feedback', '')
        simulation.strengths = evaluation.get('strengths', [])
        simulation.improvements = evaluation.get('improvements', [])
        simulation.recommended_practice = evaluation.get('recommended_practice', [])
        
        simulation.save()
        
        # Attribuer points
        self._award_points(simulation)
    
    def _generate_company_context(self, opportunity: Opportunity) -> Dict:
        """Génère le contexte entreprise avec IA"""
        return {
            'company_name': opportunity.organization,
            'recruiter_name': self._generate_recruiter_name(),
            'recruiter_role': 'Responsable Recrutement',
            'position': opportunity.title,
            'company_culture': 'Dynamique et innovante'
        }
    
    def _generate_opening_message(self, simulation: InterviewSimulation) -> str:
        """Génère le message d'ouverture du recruteur"""
        context = simulation.company_context
        return f"Bonjour ! Je suis {context['recruiter_name']}, {context['recruiter_role']} chez {context['company_name']}. Merci d'avoir postulé pour le poste de {context['position']}. Commençons par faire connaissance. Pouvez-vous vous présenter brièvement ?"
    
    def _get_elapsed_seconds(self, simulation: InterviewSimulation) -> int:
        """Calcule le temps écoulé depuis le début"""
        if not simulation.started_at:
            return 0
        delta = timezone.now() - simulation.started_at
        return int(delta.total_seconds())
    
    def _should_end_interview(self, simulation: InterviewSimulation) -> bool:
        """Détermine si l'entretien doit se terminer"""
        elapsed = self._get_elapsed_seconds(simulation)
        max_duration = simulation.duration_minutes * 60
        
        return (
            elapsed >= max_duration or
            len(simulation.conversation) >= 20  # Max 10 échanges
        )
    
    def _award_points(self, simulation: InterviewSimulation):
        """Attribue des points selon la performance"""
        from apps.credibility.models import CredibilityPoints, PointsHistory
        
        base_points = 50
        score_multiplier = simulation.overall_score / 100
        total_points = int(base_points * score_multiplier)
        
        cred, _ = CredibilityPoints.objects.get_or_create(user=simulation.user)
        cred.add_points(total_points)
        
        PointsHistory.objects.create(
            user=simulation.user,
            operation='add',
            points=total_points,
            source='other',
            description=f"Simulation entretien - Score: {simulation.overall_score:.0f}%"
        )
    
    @staticmethod
    def _generate_recruiter_name() -> str:
        """Génère un nom de recruteur ivoirien réaliste"""
        import random
        first_names = ['Fatou', 'Kouassi', 'Aya', 'Yao', 'Aminata', 'Koné']
        last_names = ['Diallo', 'Touré', 'Bamba', 'Kouadio', 'N\'Guessan']
        return f"{random.choice(first_names)} {random.choice(last_names)}"