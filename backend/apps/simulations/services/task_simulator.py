"""
OpportuCI - Task Simulator Service
===================================
Génération et gestion des simulations de tâches
"""
from typing import Dict, Optional
from django.contrib.auth import get_user_model
from apps.simulations.models import ProfessionalTaskSimulation, UserTaskAttempt
from apps.ai.services.gemini_service import GeminiAIService
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class TaskSimulatorService:
    """Service pour créer et gérer les simulations de tâches"""
    
    def __init__(self):
        self.gemini = GeminiAIService()
    
    def generate_contextual_task(
        self,
        skill: str,
        user: User,
        difficulty: str = 'intermediate'
    ) -> Optional[ProfessionalTaskSimulation]:
        """
        Génère une tâche contextualisée avec l'IA
        
        Args:
            skill: Compétence à pratiquer
            user: Utilisateur cible
            difficulty: Niveau de difficulté
            
        Returns:
            ProfessionalTaskSimulation ou None
        """
        prompt = f"""
        Crée une simulation de tâche professionnelle pour développer: {skill}
        
        PROFIL UTILISATEUR:
        - Niveau: {getattr(user, 'education_level', 'Débutant')}
        - Localisation: {getattr(user, 'city', 'Abidjan')}, Côte d'Ivoire
        
        CONTRAINTES:
        - Scénario basé sur entreprise/contexte ivoirien réaliste
        - Tâche réalisable en 20-30 minutes
        - Évaluation objective possible
        - Données et templates fournis
        - Difficulté: {difficulty}
        
        EXEMPLES DE CONTEXTES:
        - Maquis/restaurant à Abidjan
        - Boutique de téléphonie mobile
        - Startup tech locale (Yam Pukri, Julaya, etc.)
        - ONG ou association
        - PME import-export
        
        Génère en JSON strict:
        {{
            "title": "Titre attractif",
            "task_type": "excel_analysis",
            "scenario": "Description détaillée de la situation (3-4 phrases)",
            "company_context": {{
                "company_name": "Nom réaliste",
                "company_type": "Type",
                "your_role": "Ton rôle",
                "situation": "Contexte spécifique"
            }},
            "objectives": ["Objectif 1", "Objectif 2"],
            "deliverables": [
                {{"name": "Livrable 1", "description": "...", "format": "Excel/PDF"}}
            ],
            "provided_data": {{
                "description": "Ce qui est fourni",
                "sample_data": {{}}
            }},
            "evaluation_criteria": [
                {{"criterion": "Exactitude", "weight": 40, "description": "..."}}
            ],
            "time_limit_minutes": 25,
            "points_reward": 100
        }}
        """
        
        try:
            response = self.gemini.model.generate_content(prompt)
            import json
            task_data = json.loads(response.text.strip())
            
            # Créer la tâche
            task = ProfessionalTaskSimulation.objects.create(
                title=task_data['title'],
                task_type=task_data.get('task_type', 'excel_analysis'),
                description=task_data.get('scenario', ''),
                scenario=task_data.get('scenario', ''),
                company_context=task_data.get('company_context', {}),
                objectives=task_data.get('objectives', []),
                deliverables=task_data.get('deliverables', []),
                provided_data=task_data.get('provided_data', {}),
                evaluation_criteria=task_data.get('evaluation_criteria', []),
                time_limit_minutes=task_data.get('time_limit_minutes', 25),
                difficulty=difficulty,
                points_reward=task_data.get('points_reward', 100),
                created_by=user
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Erreur génération tâche: {e}", exc_info=True)
            return None
    
    def start_attempt(
        self,
        user: User,
        task: ProfessionalTaskSimulation
    ) -> UserTaskAttempt:
        """
        Démarre une nouvelle tentative
        
        Args:
            user: Utilisateur
            task: Tâche à démarrer
            
        Returns:
            UserTaskAttempt
        """
        attempt = UserTaskAttempt.objects.create(
            user=user,
            task=task,
            status='in_progress'
        )
        
        return attempt
    
    def submit_work(
        self,
        attempt: UserTaskAttempt,
        work_data: dict
    ):
        """
        Soumet le travail pour évaluation
        
        Args:
            attempt: Tentative en cours
            work_data: Données du travail soumis
        """
        from django.utils import timezone
        from .evaluation_service import EvaluationService
        
        attempt.submitted_work = work_data
        attempt.submission_time = timezone.now()
        
        # Calculer temps pris
        time_delta = attempt.submission_time - attempt.started_at
        attempt.time_taken_minutes = int(time_delta.total_seconds() / 60)
        
        attempt.status = 'submitted'
        attempt.save()
        
        # Évaluer automatiquement
        evaluator = EvaluationService()
        evaluation = evaluator.evaluate_task_attempt(attempt)
        
        attempt.score = evaluation.get('overall_score', 0)
        attempt.detailed_scores = evaluation.get('detailed_scores', {})
        attempt.ai_feedback = evaluation.get('specific_feedback', '')
        attempt.status = 'evaluated'
        attempt.completed_at = timezone.now()
        attempt.save()
        
        # Mettre à jour stats de la tâche
        self._update_task_stats(attempt.task)
        
        # Attribuer points
        self._award_points(attempt)
    
    def _update_task_stats(self, task: ProfessionalTaskSimulation):
        """Met à jour les statistiques de la tâche"""
        from django.db.models import Avg, Count
        
        stats = UserTaskAttempt.objects.filter(
            task=task,
            status='evaluated'
        ).aggregate(
            total=Count('id'),
            avg_score=Avg('score'),
            avg_time=Avg('time_taken_minutes')
        )
        
        task.total_attempts = stats['total'] or 0
        task.average_score = stats['avg_score'] or 0.0
        task.average_completion_time = int(stats['avg_time'] or 0)
        task.save()
    
    def _award_points(self, attempt: UserTaskAttempt):
        """Attribue des points selon la performance"""
        from apps.credibility.models import CredibilityPoints, PointsHistory
        
        base_points = attempt.task.points_reward
        score_multiplier = (attempt.score or 0) / 100
        
        # Bonus si dans les temps
        time_bonus = 1.2 if attempt.time_taken_minutes <= attempt.task.time_limit_minutes else 1.0
        
        total_points = int(base_points * score_multiplier * time_bonus)
        
        cred, _ = CredibilityPoints.objects.get_or_create(user=attempt.user)
        cred.add_points(total_points)
        
        PointsHistory.objects.create(
            user=attempt.user,
            operation='add',
            points=total_points,
            source='other',
            description=f"Tâche pro: {attempt.task.title} - {attempt.score:.0f}%"
        )