from django.contrib.contenttypes.models import ContentType
from .models import Notification

def create_notification(user, title, message, notification_type, related_object=None, link=None, extra_data=None):
    """
    Créer une notification pour un utilisateur
    
    Args:
        user: Utilisateur destinataire
        title: Titre de la notification
        message: Message détaillé
        notification_type: Type de notification (parmi les choix définis)
        related_object: Objet relié (opportunité, formation, etc.) - optionnel
        link: Lien URL - optionnel
        extra_data: Données supplémentaires en format JSON - optionnel
    
    Returns:
        Notification créée
    """
    notification = Notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        extra_data=extra_data
    )
    
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        notification.content_type = content_type
        notification.object_id = related_object.id
    
    notification.save()
    return notification

def notify_opportunity_deadline(opportunity, days_before=3):
    """
    Envoyer des notifications pour les échéances d'opportunités
    
    Args:
        opportunity: Opportunité concernée
        days_before: Nombre de jours avant l'échéance pour notifier
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.opportunities.models import UserOpportunity
    
    # Ne pas envoyer de notifications si pas de deadline ou si déjà expirée
    if not opportunity.deadline or opportunity.is_expired:
        return
    
    # Calculer la date de notification
    notification_date = opportunity.deadline - timedelta(days=days_before)
    
    # Vérifier si c'est le moment d'envoyer la notification
    if timezone.now().date() == notification_date.date():
        # Récupérer tous les utilisateurs ayant sauvegardé ou postulé à cette opportunité
        users = UserOpportunity.objects.filter(
            opportunity=opportunity,
            relation_type__in=['saved', 'applied']
        ).values_list('user', flat=True).distinct()
        
        for user_id in users:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            create_notification(
                user=user,
                title=f"Rappel: {opportunity.title}",
                message=f"L'opportunité {opportunity.title} se termine dans {days_before} jours.",
                notification_type='deadline_reminder',
                related_object=opportunity,
                extra_data={'days_remaining': days_before}
            )