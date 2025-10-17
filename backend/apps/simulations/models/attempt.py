"""
OpportuCI - Task Attempt Models
================================
Tentatives utilisateur sur les tâches
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class UserTaskAttempt(models.Model):
    """Tentative d'un utilisateur sur une tâche"""
    
    STATUS_CHOICES = [
        ('in_progress', _('En cours')),
        ('submitted', _('Soumis')),
        ('evaluated', _('Évalué')),
        ('needs_revision', _('À réviser')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_attempts',
        verbose_name=_('utilisateur')
    )
    
    task = models.ForeignKey(
        'ProfessionalTaskSimulation',
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('tâche')
    )
    
    # Soumission
    submitted_work = models.JSONField(
        default=dict,
        verbose_name=_('travail soumis'),
        help_text=_('Fichiers, réponses, livrables')
    )
    
    submission_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('heure de soumission')
    )
    
    time_taken_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('temps pris (minutes)')
    )
    
    # État
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name=_('statut')
    )
    
    # Évaluation
    score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_('score')
    )
    
    detailed_scores = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('scores détaillés par critère')
    )
    
    ai_feedback = models.TextField(
        blank=True,
        verbose_name=_('feedback IA')
    )
    
    mentor_feedback = models.TextField(
        blank=True,
        verbose_name=_('feedback mentor')
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'simulations'
        verbose_name = _('tentative de tâche')
        verbose_name_plural = _('tentatives de tâches')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['task', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title[:30]}"