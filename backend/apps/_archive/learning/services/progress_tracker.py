"""
OpportuCI - Progress Tracking Service
======================================
Service de suivi détaillé de la progression d'apprentissage
"""
import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from apps.learning.models import (
    PersonalizedLearningJourney,
    MicroLearningModule,
    UserModuleProgress,
    JourneyModule
)
from apps.credibility.models import CredibilityPoints, PointsHistory
from apps.notifications.services import create_notification

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Service de tracking de progression avec gamification"""
    
    def __init__(self):
        self.completion_threshold = 90  # 90% = complété
    
    @transaction.atomic
    def start_module(self, user, module: MicroLearningModule) -> UserModuleProgress:
        """
        Démarre un module pour un utilisateur
        
        Returns:
            UserModuleProgress object
        """
        progress, created = UserModuleProgress.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now()
            }
        )
        
        if created:
            # Première tentative
            progress.attempts = 1
            progress.started_at = timezone.now()
            progress.status = 'in_progress'
        else:
            # Reprise
            if progress.status == 'not_started':
                progress.status = 'in_progress'
                progress.started_at = timezone.now()
            progress.attempts += 1
        
        progress.save()
        
        # Mettre à jour le JourneyModule si existe
        self._update_journey_module_start(user, module)
        
        logger.info(f"User {user.id} started module {module.id}")
        return progress
    
    @transaction.atomic
    def update_progress(
        self, 
        user, 
        module: MicroLearningModule, 
        percentage: int, 
        time_spent_seconds: int = 0
    ) -> UserModuleProgress:
        """
        Met à jour la progression sur un module
        
        Args:
            percentage: Progression 0-100
            time_spent_seconds: Temps passé en secondes
        """
        progress = UserModuleProgress.objects.get(user=user, module=module)
        
        # Mettre à jour progression
        progress.progress_percentage = min(100, max(0, percentage))
        progress.time_spent_minutes += time_spent_seconds // 60
        progress.last_accessed = timezone.now()
        
        # Auto-completion si seuil atteint
        if progress.progress_percentage >= self.completion_threshold and not progress.completed_at:
            return self.complete_module(user, module, score=progress.progress_percentage)
        
        progress.save()
        
        # Mettre à jour JourneyModule
        self._update_journey_module_progress(user, module, time_spent_seconds)
        
        return progress
    
    @transaction.atomic
    def complete_module(
        self, 
        user, 
        module: MicroLearningModule, 
        score: float,
        feedback: Optional[str] = None
    ) -> UserModuleProgress:
        """
        Marque un module comme complété
        
        Args:
            score: Score obtenu (0-100)
            feedback: Feedback optionnel de l'IA
        """
        progress = UserModuleProgress.objects.get(user=user, module=module)
        
        # Mettre à jour le statut
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.progress_percentage = 100
        
        # Score
        progress.last_score = score
        progress.best_score = max(progress.best_score or 0, score)
        
        # Feedback IA si fourni
        if feedback:
            progress.ai_feedback = feedback
        
        progress.save()
        
        # Mettre à jour statistiques du module
        self._update_module_stats(module, score, progress.time_spent_minutes)
        
        # Mettre à jour JourneyModule
        journey_module = self._complete_journey_module(user, module, score)
        
        # Récompenses
        self._award_completion_rewards(user, module, score)
        
        # Vérifier complétion du journey
        if journey_module:
            self._check_journey_completion(user, journey_module.journey)
        
        # Notification
        self._send_completion_notification(user, module, score)
        
        logger.info(f"User {user.id} completed module {module.id} with score {score}")
        return progress
    
    def get_user_stats(self, user, period_days: int = 30) -> Dict:
        """
        Récupère les statistiques d'apprentissage de l'utilisateur
        
        Args:
            period_days: Période en jours (défaut 30)
        """
        from django.db.models import Sum, Avg, Count, Q
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Modules
        modules_stats = UserModuleProgress.objects.filter(
            user=user,
            started_at__gte=start_date
        ).aggregate(
            total_modules=Count('id'),
            completed_modules=Count('id', filter=Q(status='completed')),
            total_time_minutes=Sum('time_spent_minutes'),
            avg_score=Avg('best_score', filter=Q(status='completed'))
        )
        
        # Journeys
        journeys = PersonalizedLearningJourney.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        active_journeys = journeys.filter(status='in_progress').count()
        completed_journeys = journeys.filter(status='completed').count()
        
        # Streak
        streak = self._calculate_learning_streak(user)
        
        # Compétences acquises
        skills_acquired = self._get_skills_acquired(user, start_date)
        
        return {
            'period_days': period_days,
            'modules': {
                'total': modules_stats['total_modules'] or 0,
                'completed': modules_stats['completed_modules'] or 0,
                'completion_rate': round(
                    (modules_stats['completed_modules'] / modules_stats['total_modules'] * 100)
                    if modules_stats['total_modules'] else 0, 1
                ),
                'avg_score': round(modules_stats['avg_score'] or 0, 1),
                'total_hours': round((modules_stats['total_time_minutes'] or 0) / 60, 1)
            },
            'journeys': {
                'active': active_journeys,
                'completed': completed_journeys,
                'total': journeys.count()
            },
            'streak_days': streak,
            'skills_acquired': skills_acquired,
            'rank_info': self._get_user_rank(user)
        }
    
    def get_journey_progress_detail(self, journey: PersonalizedLearningJourney) -> Dict:
        """Récupère le détail de progression d'un parcours"""
        
        journey_modules = JourneyModule.objects.filter(
            journey=journey
        ).select_related('module').order_by('order')
        
        total_modules = journey_modules.count()
        completed_modules = journey_modules.filter(completed=True).count()
        
        # Modules par priorité
        critical_total = journey_modules.filter(priority='critical').count()
        critical_done = journey_modules.filter(priority='critical', completed=True).count()
        
        high_total = journey_modules.filter(priority='high').count()
        high_done = journey_modules.filter(priority='high', completed=True).count()
        
        # Temps
        total_time_spent = journey_modules.aggregate(
            Sum('time_spent_minutes')
        )['time_spent_minutes__sum'] or 0
        
        # Score moyen
        avg_score = journey_modules.filter(
            best_score__isnull=False
        ).aggregate(Avg('best_score'))['best_score__avg']
        
        return {
            'journey_id': journey.id,
            'status': journey.status,
            'overall_progress': {
                'percentage': journey.progress_percentage,
                'modules_completed': completed_modules,
                'modules_total': total_modules,
                'hours_spent': round(total_time_spent / 60, 1),
                'hours_estimated': journey.total_estimated_hours
            },
            'by_priority': {
                'critical': {'done': critical_done, 'total': critical_total},
                'high': {'done': high_done, 'total': high_total}
            },
            'performance': {
                'avg_score': round(avg_score or 0, 1),
                'success_probability': journey.success_probability
            },
            'timeline': {
                'started_at': journey.started_at,
                'estimated_completion': journey.estimated_completion_date,
                'last_activity': journey.last_activity
            }
        }
    
    # ========== MÉTHODES PRIVÉES ==========
    
    def _update_journey_module_start(self, user, module):
        """Met à jour le JourneyModule au démarrage"""
        journey_module = JourneyModule.objects.filter(
            journey__user=user,
            module=module,
            journey__status='in_progress'
        ).first()
        
        if journey_module and not journey_module.started:
            journey_module.started = True
            journey_module.started_at = timezone.now()
            journey_module.save()
    
    def _update_journey_module_progress(self, user, module, time_spent_seconds):
        """Met à jour la progression du JourneyModule"""
        journey_module = JourneyModule.objects.filter(
            journey__user=user,
            module=module,
            journey__status='in_progress'
        ).first()
        
        if journey_module:
            journey_module.time_spent_minutes += time_spent_seconds // 60
            journey_module.save()
            
            # Mettre à jour le journey parent
            self._update_journey_progress(journey_module.journey)
    
    def _complete_journey_module(self, user, module, score) -> Optional[JourneyModule]:
        """Marque le JourneyModule comme complété"""
        journey_module = JourneyModule.objects.filter(
            journey__user=user,
            module=module,
            journey__status='in_progress'
        ).first()
        
        if journey_module:
            journey_module.completed = True
            journey_module.completed_at = timezone.now()
            journey_module.best_score = max(journey_module.best_score or 0, score)
            journey_module.save()
            
            return journey_module
        
        return None
    
    def _update_journey_progress(self, journey: PersonalizedLearningJourney):
        """Recalcule la progression globale du journey"""
        journey_modules = JourneyModule.objects.filter(journey=journey)
        
        total = journey_modules.count()
        completed = journey_modules.filter(completed=True).count()
        
        if total > 0:
            journey.progress_percentage = int((completed / total) * 100)
            
            # Temps passé
            total_time = journey_modules.aggregate(
                Sum('time_spent_minutes')
            )['time_spent_minutes__sum'] or 0
            journey.hours_completed = round(total_time / 60, 1)
            
            journey.last_activity = timezone.now()
            journey.save()
    
    def _check_journey_completion(self, user, journey: PersonalizedLearningJourney):
        """Vérifie si le journey est complété"""
        mandatory_modules = JourneyModule.objects.filter(
            journey=journey,
            is_mandatory=True
        )
        
        all_completed = not mandatory_modules.filter(completed=False).exists()
        
        if all_completed and journey.status != 'completed':
            journey.status = 'completed'
            journey.completed_at = timezone.now()
            journey.save()
            
            # Récompense spéciale pour journey complété
            self._award_journey_completion_rewards(user, journey)
            
            logger.info(f"Journey {journey.id} completed by user {user.id}")
    
    def _update_module_stats(self, module: MicroLearningModule, score: float, time_minutes: int):
        """Met à jour les stats du module"""
        module.total_completions += 1
        
        # Moyenne score
        total_score = module.average_score * (module.total_completions - 1) + score
        module.average_score = total_score / module.total_completions
        
        # Moyenne temps
        total_time = module.average_time_minutes * (module.total_completions - 1) + time_minutes
        module.average_time_minutes = int(total_time / module.total_completions)
        
        # Taux de succès (score >= 70)
        if score >= 70:
            success_count = int(module.success_rate * (module.total_completions - 1) / 100) + 1
            module.success_rate = (success_count / module.total_completions) * 100
        
        module.save()
    
    def _award_completion_rewards(self, user, module: MicroLearningModule, score: float):
        """Attribue les récompenses pour complétion de module"""
        # Points de base
        base_points = module.points_reward
        
        # Bonus selon score
        if score >= 90:
            bonus = int(base_points * 0.5)
        elif score >= 80:
            bonus = int(base_points * 0.3)
        elif score >= 70:
            bonus = int(base_points * 0.1)
        else:
            bonus = 0
        
        total_points = base_points + bonus
        
        # Créditer les points
        cred, _ = CredibilityPoints.objects.get_or_create(user=user)
        cred.add_points(total_points)
        
        PointsHistory.objects.create(
            user=user,
            operation='add',
            points=total_points,
            source='course_completion',
            description=f"Module complété: {module.title} ({score}%)"
        )
    
    def _award_journey_completion_rewards(self, user, journey: PersonalizedLearningJourney):
        """Récompenses pour journey complété"""
        # Gros bonus de points
        bonus_points = 200
        
        cred, _ = CredibilityPoints.objects.get_or_create(user=user)
        cred.add_points(bonus_points)
        
        PointsHistory.objects.create(
            user=user,
            operation='add',
            points=bonus_points,
            source='other',
            description=f"Parcours complété: {journey.target_opportunity.title}"
        )
        
        # Notification spéciale
        create_notification(
            user=user,
            title="🎉 Parcours complété !",
            message=f"Bravo ! Tu as terminé le parcours pour {journey.target_opportunity.title}. "
                   f"Tu es maintenant prêt à candidater ! +{bonus_points} points",
            notification_type='achievement'
        )
    
    def _send_completion_notification(self, user, module: MicroLearningModule, score: float):
        """Notification de complétion de module"""
        emoji = "🌟" if score >= 90 else "👍" if score >= 70 else "💪"
        
        create_notification(
            user=user,
            title=f"{emoji} Module complété !",
            message=f"Tu as terminé '{module.title}' avec un score de {score}%. Continue comme ça !",
            notification_type='achievement'
        )
    
    def _calculate_learning_streak(self, user) -> int:
        """Calcule la série de jours consécutifs d'apprentissage"""
        from datetime import date, timedelta
        
        # Récupérer dates d'activité
        activity_dates = UserModuleProgress.objects.filter(
            user=user,
            last_accessed__isnull=False
        ).dates('last_accessed', 'day', order='DESC')
        
        if not activity_dates:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for activity_date in activity_dates:
            expected_date = current_date - timedelta(days=streak)
            
            if activity_date == expected_date:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_skills_acquired(self, user, start_date) -> List[str]:
        """Liste des compétences acquises dans la période"""
        completed_modules = UserModuleProgress.objects.filter(
            user=user,
            status='completed',
            completed_at__gte=start_date,
            best_score__gte=70  # Minimum 70% pour considérer skill acquise
        ).select_related('module')
        
        skills = set()
        for progress in completed_modules:
            skills.add(progress.module.skill_taught)
        
        return sorted(list(skills))
    
    def _get_user_rank(self, user) -> Dict:
        """Calcule le rang de l'utilisateur"""
        try:
            cred = CredibilityPoints.objects.get(user=user)
            
            better_users = CredibilityPoints.objects.filter(
                points__gt=cred.points
            ).count()
            
            total_users = CredibilityPoints.objects.count()
            
            percentile = 100 - int((better_users / total_users) * 100) if total_users > 0 else 50
            
            return {
                'points': cred.points,
                'level': cred.level,
                'percentile': percentile,
                'rank': better_users + 1,
                'total_users': total_users
            }
        except CredibilityPoints.DoesNotExist:
            return {
                'points': 0,
                'level': 1,
                'percentile': 50,
                'rank': 0,
                'total_users': 0
            }