"""
OpportuCI - Evaluation Service
===============================
Évaluation automatique des performances
"""
from typing import Dict, Optional
from apps.simulations.models import UserTaskAttempt
from apps.ai.services.gemini_service import GeminiAIService
import logging

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service d'évaluation des tâches professionnelles"""
    
    def __init__(self):
        self.gemini = GeminiAIService()
    
    def evaluate_task_attempt(self, attempt: UserTaskAttempt) -> Dict:
        """
        Évalue une tentative de tâche avec l'IA
        
        Args:
            attempt: Tentative à évaluer
            
        Returns:
            Dict avec score, feedback, scores détaillés
        """
        task = attempt.task
        
        prompt = f"""
        Évalue ce travail professionnel selon les critères définis.
        
        TÂCHE: {task.title}
        TYPE: {task.get_task_type_display()}
        CONTEXTE: {task.scenario}
        
        CRITÈRES D'ÉVALUATION:
        {self._format_criteria(task.evaluation_criteria)}
        
        TRAVAIL SOUMIS:
        {self._format_submitted_work(attempt.submitted_work)}
        
        TEMPS PRIS: {attempt.time_taken_minutes} min (limite: {task.time_limit_minutes} min)
        
        Évalue en JSON strict:
        {{
            "overall_score": 75,
            "detailed_scores": {{
                "exactitude": 80,
                "presentation": 70,
                "respect_consignes": 85
            }},
            "strengths": ["Point fort 1", "Point fort 2"],
            "improvements": ["Amélioration 1", "Amélioration 2"],
            "specific_feedback": "Feedback détaillé (3-4 phrases)",
            "professional_tips": ["Conseil pro 1", "Conseil pro 2"],
            "would_hire": true,
            "reasoning": "Justification de l'évaluation"
        }}
        
        Sois juste mais encourageant. C'est un exercice d'apprentissage.
        """
        
        try:
            evaluation = self.gemini.model.generate_content(prompt)
            import json
            result = json.loads(evaluation.text.strip())
            return result
        except Exception as e:
            logger.error(f"Erreur évaluation tâche: {e}", exc_info=True)
            # Fallback
            return {
                "overall_score": 60,
                "detailed_scores": {},
                "strengths": ["Tentative complétée"],
                "improvements": ["Continuer à pratiquer"],
                "specific_feedback": "Merci d'avoir complété cette tâche.",
                "professional_tips": ["Prendre plus de temps pour les détails"],
                "would_hire": False,
                "reasoning": "Évaluation automatique non disponible"
            }
    
    def _format_criteria(self, criteria: list) -> str:
        """Formate les critères pour le prompt"""
        formatted = []
        for crit in criteria:
            formatted.append(
                f"- {crit.get('criterion', 'N/A')}: "
                f"{crit.get('weight', 0)}% - {crit.get('description', '')}"
            )
        return "\n".join(formatted)
    
    def _format_submitted_work(self, work: dict) -> str:
        """Formate le travail soumis pour le prompt"""
        if not work:
            return "Aucun travail soumis"
        
        formatted = []
        for key, value in work.items():
            formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)