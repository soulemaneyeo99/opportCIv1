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
    """
    Simulation d'entretien d'embauche avec IA

    Permet aux utilisateurs de s'entraîner pour leurs entretiens
    avec un recruteur IA qui s'adapte au contexte de l'opportunité.
    """

    class InterviewType(models.TextChoices):
        PHONE = 'phone', _('Entretien téléphonique')
        VIDEO = 'video', _('Entretien vidéo')
        TECHNICAL = 'technical', _('Entretien technique')
        BEHAVIORAL = 'behavioral', _('Entretien comportemental')
        PANEL = 'panel', _('Panel (plusieurs recruteurs)')

    class Difficulty(models.TextChoices):
        EASY = 'easy', _('Facile - Débutant')
        MEDIUM = 'medium', _('Moyen - Intermédiaire')
        HARD = 'hard', _('Difficile - Avancé')

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', _('Programmée')
        IN_PROGRESS = 'in_progress', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        ABANDONED = 'abandoned', _('Abandonnée')

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
        _('type d\'entretien'),
        max_length=20,
        choices=InterviewType.choices,
        default=InterviewType.BEHAVIORAL
    )

    difficulty = models.CharField(
        _('difficulté'),
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )

    duration_minutes = models.PositiveIntegerField(
        _('durée prévue (minutes)'),
        default=15
    )

    # Contexte entreprise (généré par IA)
    company_context = models.JSONField(
        _('contexte entreprise'),
        default=dict,
        help_text=_('Nom recruteur, culture entreprise, etc.')
    )

    # État
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True
    )

    # Conversation (stockage des échanges)
    conversation = models.JSONField(
        _('conversation'),
        default=list,
        help_text=_('Liste des messages échangés')
    )

    # Résultats
    overall_score = models.FloatField(
        _('score global'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    detailed_scores = models.JSONField(
        _('scores détaillés'),
        default=dict,
        blank=True,
        help_text=_('Communication, technique, motivation, etc.')
    )

    ai_feedback = models.TextField(
        _('feedback IA'),
        blank=True
    )

    strengths = models.JSONField(
        _('points forts'),
        default=list,
        blank=True
    )

    improvements = models.JSONField(
        _('axes d\'amélioration'),
        default=list,
        blank=True
    )

    # Recommandations
    recommended_practice = models.JSONField(
        _('pratique recommandée'),
        default=list,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'prep'
        verbose_name = _('simulation d\'entretien')
        verbose_name_plural = _('simulations d\'entretien')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['opportunity', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.opportunity.title[:30]}"

    def add_message(self, role: str, message: str):
        """Ajoute un message à la conversation."""
        from django.utils import timezone
        self.conversation.append({
            'role': role,
            'message': message,
            'timestamp': timezone.now().isoformat()
        })
        self.save(update_fields=['conversation'])

    def complete(self, scores: dict, feedback: str):
        """Marque la simulation comme terminée avec les résultats."""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.overall_score = scores.get('overall_score')
        self.detailed_scores = scores.get('detailed_scores', {})
        self.strengths = scores.get('strengths', [])
        self.improvements = scores.get('improvements', [])
        self.ai_feedback = feedback
        self.save()
