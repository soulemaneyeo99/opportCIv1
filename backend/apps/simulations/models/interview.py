"""
OpportuCI - Interview Simulation Models
========================================
Simulations d'entretien avec IA
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid


class InterviewSimulation(models.Model):
    """Simulation d'entretien d'embauche avec IA"""
    
    INTERVIEW_TYPES = [
        ('phone', _('Entretien téléphonique')),
        ('video', _('Entretien vidéo')),
        ('technical', _('Entretien technique')),
        ('behavioral', _('Entretien comportemental')),
        ('panel', _('Panel (plusieurs recruteurs)')),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', _('Facile - Débutant')),
        ('medium', _('Moyen - Intermédiaire')),
        ('hard', _('Difficile - Avancé')),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', _('Programmée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
        ('abandoned', _('Abandonnée')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_simulations',
        verbose_name=_('utilisateur')
    )
    
    opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.CASCADE,
        related_name='interview_simulations',
        verbose_name=_('opportunité')
    )
    
    # Configuration
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPES,
        default='behavioral',
        verbose_name=_('type d\'entretien')
    )
    
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='medium',
        verbose_name=_('difficulté')
    )
    
    duration_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name=_('durée prévue (minutes)')
    )
    
    # Contexte entreprise (généré par IA)
    company_context = models.JSONField(
        default=dict,
        verbose_name=_('contexte entreprise'),
        help_text=_('Nom recruteur, culture entreprise, etc.')
    )
    
    # État
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('statut')
    )
    
    # Conversation (stockage des échanges)
    conversation = models.JSONField(
        default=list,
        verbose_name=_('conversation'),
        help_text=_('Liste des messages échangés')
    )
    
    # Résultats
    overall_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_('score global')
    )
    
    detailed_scores = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('scores détaillés'),
        help_text=_('Communication, technique, motivation, etc.')
    )
    
    ai_feedback = models.TextField(
        blank=True,
        verbose_name=_('feedback IA')
    )
    
    strengths = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('points forts')
    )
    
    improvements = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('axes d\'amélioration')
    )
    
    # Recommandations
    recommended_practice = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('pratique recommandée')
    )
    
    follow_up_modules = models.ManyToManyField(
        'learning.MicroLearningModule',
        blank=True,
        related_name='interview_followups',
        verbose_name=_('modules de suivi recommandés')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'simulations'
        verbose_name = _('simulation d\'entretien')
        verbose_name_plural = _('simulations d\'entretien')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['opportunity', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title[:30]}"