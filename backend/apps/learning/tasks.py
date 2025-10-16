
# ===================================================================
# apps/learning/tasks.py - Celery Tasks
# ===================================================================

"""
OpportuCI - Learning Celery Tasks
==================================
Tâches asynchrones pour le système d'apprentissage
"""
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_opportunity_task(self, opportunity_id):
    """
    Analyse une opportunité avec Gemini AI (async)
    
    Args:
        opportunity_id: ID de l'opportunité à analyser
    """
    from apps.opportunities.models import Opportunity
    from apps.learning.services.intelligence_service import OpportunityIntelligenceService
    
    try:
        opportunity = Opportunity.objects.get(id=opportunity_id)
        service = OpportunityIntelligenceService()
        
        result = service.analyze_opportunity(opportunity, force_refresh=True)
        
        if result:
            logger.info(f"Successfully analyzed opportunity {opportunity_id}")
            return {
                'status': 'success',
                'opportunity_id': opportunity_id,
                'skills_found': len(result.extracted_skills.get('technical', []))
            }
        else:
            logger.error(f"Failed to analyze opportunity {opportunity_id}")
            return {'status': 'error', 'message': 'Analysis failed'}
            
    except Opportunity.DoesNotExist:
        logger.error(f"Opportunity {opportunity_id} not found")
        return {'status': 'error', 'message': 'Opportunity not found'}
    except Exception as e:
        logger.exception(f"Error in analyze_opportunity_task: {e}")
        raise self.retry(exc=e, countdown=60)  # Retry après 1 min


@shared_task
def generate_learning_path_task(user_id, opportunity_id):
    """
    Génère un parcours d'apprentissage (async)
    
    Args:
        user_id: ID de l'utilisateur
        opportunity_id: ID de l'opportunité cible
    """
    from django.contrib.auth import get_user_model
    from apps.opportunities.models import Opportunity
    from apps.learning.services.path_generator import LearningPathGenerator
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        opportunity = Opportunity.objects.get(id=opportunity_id)
        
        generator = LearningPathGenerator()
        journey = generator.generate_journey(user, opportunity)
        
        if journey:
            logger.info(f"Generated journey {journey.id} for user {user_id}")
            return {
                'status': 'success',
                'journey_id': str(journey.id),
                'modules_count': journey.learning_modules.count()
            }
        else:
            logger.error(f"Failed to generate journey for user {user_id}")
            return {'status': 'error'}
            
    except Exception as e:
        logger.exception(f"Error generating journey: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_module_metrics_task(module_id):
    """
    Met à jour les métriques d'un module
    
    Args:
        module_id: ID du module
    """
    from apps.learning.models import MicroLearningModule, UserModuleProgress
    from django.db.models import Avg, Count
    
    try:
        module = MicroLearningModule.objects.get(id=module_id)
        
        # Statistiques des progressions
        stats = UserModuleProgress.objects.filter(
            module=module,
            status='completed'
        ).aggregate(
            total=Count('id'),
            avg_score=Avg('best_score'),
            avg_time=Avg('time_spent_minutes')
        )
        
        module.total_completions = stats['total'] or 0
        module.average_score = stats['avg_score'] or 0.0
        module.average_time_minutes = int(stats['avg_time'] or 0)
        
        # Taux de réussite (score >= 70)
        success_count = UserModuleProgress.objects.filter(
            module=module,
            status='completed',
            best_score__gte=70
        ).count()
        
        if stats['total']:
            module.success_rate = (success_count / stats['total']) * 100
        
        module.save()
        
        logger.info(f"Updated metrics for module {module_id}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Error updating module metrics: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_learning_reminders():
    """
    Envoie des rappels d'apprentissage aux utilisateurs inactifs
    Tâche périodique (daily)
    """
    from django.contrib.auth import get_user_model
    from apps.learning.models import PersonalizedLearningJourney
    from apps.notifications.services import create_notification
    from datetime import timedelta
    
    User = get_user_model()
    cutoff_date = timezone.now() - timedelta(days=3)
    
    # Trouver utilisateurs avec journeys actifs mais inactifs depuis 3 jours
    inactive_journeys = PersonalizedLearningJourney.objects.filter(
        status='in_progress',
        last_activity__lt=cutoff_date
    ).select_related('user', 'target_opportunity')
    
    count = 0
    for journey in inactive_journeys:
        try:
            create_notification(
                user=journey.user,
                title="On t'attend ! 📚",
                message=f"Ça fait 3 jours que tu n'as pas continué ton parcours pour {journey.target_opportunity.title}. Juste 15 minutes aujourd'hui ? 💪",
                notification_type='system',
                extra_data={'journey_id': str(journey.id)}
            )
            count += 1
        except Exception as e:
            logger.error(f"Error sending reminder to user {journey.user.id}: {e}")
    
    logger.info(f"Sent {count} learning reminders")
    return {'status': 'success', 'reminders_sent': count}


@shared_task
def calculate_journey_progress_task(journey_id):
    """
    Recalcule la progression d'un parcours
    
    Args:
        journey_id: ID du parcours
    """
    from apps.learning.models import PersonalizedLearningJourney
    
    try:
        journey = PersonalizedLearningJourney.objects.get(id=journey_id)
        journey.update_progress()
        
        logger.info(f"Updated progress for journey {journey_id}")
        return {
            'status': 'success',
            'progress': journey.progress_percentage
        }
    except Exception as e:
        logger.exception(f"Error calculating journey progress: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_ai_feedback():
    """
    Nettoie les anciens feedbacks IA (>30 jours)
    Tâche périodique (weekly)
    """
    from apps.learning.models import UserModuleProgress
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    updated = UserModuleProgress.objects.filter(
        ai_analysis_date__lt=cutoff_date
    ).update(
        ai_feedback='',
        personalized_hints=[],
        ai_analysis_date=None
    )
    
    logger.info(f"Cleaned {updated} old AI feedbacks")
    return {'status': 'success', 'cleaned': updated}

