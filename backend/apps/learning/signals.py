# ===================================================================
# apps/learning/signals.py - Django Signals
# ===================================================================

"""
OpportuCI - Learning Signals
=============================
Signaux pour réagir aux événements du système
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from apps.learning.models import (
    UserModuleProgress,
    JourneyModule,
    PersonalizedLearningJourney
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserModuleProgress)
def on_module_progress_update(sender, instance, created, **kwargs):
    """
    Réagit aux mises à jour de progression sur un module
    """
    # Si module complété, mettre à jour le JourneyModule correspondant
    if instance.status == 'completed' and instance.completed_at:
        journey_modules = JourneyModule.objects.filter(
            journey__user=instance.user,
            module=instance.module,
            completed=False
        )
        
        for jm in journey_modules:
            jm.mark_completed(
                score=instance.best_score,
                time_spent=instance.time_spent_minutes
            )


@receiver(post_save, sender=JourneyModule)
def on_journey_module_completed(sender, instance, created, **kwargs):
    """
    Réagit à la complétion d'un module dans un parcours
    """
    if not created and instance.completed:
        # Mettre à jour la progression du parcours
        instance.journey.update_progress()
        
        # Vérifier si c'était le dernier module
        remaining = JourneyModule.objects.filter(
            journey=instance.journey,
            is_mandatory=True,
            completed=False
        ).count()
        
        if remaining == 0:
            # Parcours terminé !
            instance.journey.status = 'completed'
            instance.journey.completed_at = timezone.now()
            instance.journey.save()
            
            # Notification de félicitations
            from apps.notifications.services import create_notification
            create_notification(
                user=instance.journey.user,
                title="🎉 Parcours terminé !",
                message=f"Félicitations ! Tu as terminé ton parcours pour {instance.journey.target_opportunity.title}. Tu es maintenant prêt à candidater ! 🚀",
                notification_type='achievement',
                extra_data={'journey_id': str(instance.journey.id)}
            )


@receiver(pre_save, sender=PersonalizedLearningJourney)
def update_journey_timestamps(sender, instance, **kwargs):
    """
    Met à jour les timestamps du parcours
    """
    if instance.status == 'in_progress' and not instance.started_at:
        instance.started_at = timezone.now()
    
    if instance.status == 'completed' and not instance.completed_at:
        instance.completed_at = timezone.now()

