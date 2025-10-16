# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    """Modèle de notification pour les utilisateurs"""
    
    # Types de notifications
    TYPE_CHOICES = (
        ('new_opportunity', _('Nouvelle opportunité')),
        ('deadline_reminder', _('Rappel d\'échéance')),
        ('status_update', _('Mise à jour de statut')),
        ('application_update', _('Mise à jour de candidature')),
        ('system', _('Notification système')),
        ('message', _('Message')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='notifications')
    title = models.CharField(_('titre'), max_length=255)
    message = models.TextField(_('message'))
    notification_type = models.CharField(_('type'), max_length=30, choices=TYPE_CHOICES)
    is_read = models.BooleanField(_('lue'), default=False)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    
    # Pour relier à n'importe quel modèle (opportunité, formation, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                    null=True, blank=True)
    object_id = models.CharField(_('ID de l\'objet'), max_length=50, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Lien vers une URL spécifique si nécessaire
    link = models.URLField(_('lien'), blank=True, null=True)
    
    # Données supplémentaires (JSON)
    extra_data = models.JSONField(_('données supplémentaires'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.is_read = True
        self.save(update_fields=['is_read'])