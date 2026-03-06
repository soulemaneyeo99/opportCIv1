# backend/credibility/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserAchievement, CredibilityPoints, PointsHistory

User = get_user_model()

@receiver(post_save, sender=User)
def create_credibility_points(sender, instance, created, **kwargs):
    """Crée automatiquement un objet CredibilityPoints pour les nouveaux utilisateurs"""
    if created:
        CredibilityPoints.objects.create(user=instance)

@receiver(post_save, sender=UserAchievement)
def add_achievement_points(sender, instance, created, **kwargs):
    """Ajoute des points lorsqu'un utilisateur obtient une réalisation"""
    if created:
        user = instance.user
        achievement = instance.achievement
        
        # Récupérer ou créer les points de crédibilité
        credibility, _ = CredibilityPoints.objects.get_or_create(user=user)
        
        # Ajouter les points
        credibility.add_points(achievement.points)
        
        # Enregistrer l'historique
        PointsHistory.objects.create(
            user=user,
            operation='add',
            points=achievement.points,
            source='achievement',
            description=f"Réalisation obtenue: {achievement.name}"
        )