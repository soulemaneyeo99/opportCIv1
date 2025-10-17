"""
OpportuCI - Professional Task Simulation Models
================================================
Simulations de tâches professionnelles
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid


class ProfessionalTaskSimulation(models.Model):
    """Simulation de tâche professionnelle réelle"""
    
    TASK_TYPES = [
        ('excel_analysis', _('Analyse Excel')),
        ('presentation', _('Présentation PowerPoint')),
        ('email_writing', _('Rédaction email professionnel')),
        ('customer_service', _('Service client')),
        ('project_planning', _('Planification projet')),
        ('data_entry', _('Saisie de données')),
        ('social_media', _('Gestion réseaux sociaux')),
        ('coding_challenge', _('Défi de code')),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', _('Débutant')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=200, verbose_name=_('titre'))
    
    task_type = models.CharField(
        max_length=30,
        choices=TASK_TYPES,
        verbose_name=_('type de tâche')
    )
    
    description = models.TextField(verbose_name=_('description'))
    
    # Scénario contextualisé
    scenario = models.TextField(
        verbose_name=_('scénario'),
        help_text=_('Contexte de la tâche (entreprise ivoirienne fictive)')
    )
    
    company_context = models.JSONField(
        default=dict,
        verbose_name=_('contexte entreprise'),
        help_text=_('Nom entreprise, secteur, ton rôle, etc.')
    )
    
    # Objectifs
    objectives = models.JSONField(
        default=list,
        verbose_name=_('objectifs'),
        help_text=_('Liste des objectifs à atteindre')
    )
    
    deliverables = models.JSONField(
        default=list,
        verbose_name=_('livrables attendus'),
        help_text=_('Ce que l\'utilisateur doit produire')
    )
    
    # Ressources fournies
    provided_data = models.JSONField(
        default=dict,
        verbose_name=_('données fournies'),
        help_text=_('Fichiers, templates, infos nécessaires')
    )
    
    templates = models.JSONField(
        default=dict,
        verbose_name=_('templates'),
        help_text=_('Templates de départ (Excel, email, etc.)')
    )
    
    # Évaluation
    evaluation_criteria = models.JSONField(
        default=list,
        verbose_name=_('critères d\'évaluation'),
        help_text=_('Liste des critères avec poids')
    )
    
    time_limit_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_('temps limite (minutes)')
    )
    
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='intermediate',
        verbose_name=_('difficulté')
    )
    
    # Gamification
    points_reward = models.PositiveIntegerField(
        default=100,
        verbose_name=_('points récompense')
    )
    
    # Statistiques
    total_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name=_('tentatives totales')
    )
    
    average_score = models.FloatField(
        default=0.0,
        verbose_name=_('score moyen')
    )
    
    average_completion_time = models.PositiveIntegerField(
        default=0,
        verbose_name=_('temps moyen (minutes)')
    )
    
    # Gestion
    is_active = models.BooleanField(default=True, verbose_name=_('actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name=_('créé par')
    )
    
    class Meta:
        app_label = 'simulations'
        verbose_name = _('simulation tâche professionnelle')
        verbose_name_plural = _('simulations tâches professionnelles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_type', 'is_active']),
            models.Index(fields=['difficulty', 'is_active']),
        ]
    
    def __str__(self):
        return self.title