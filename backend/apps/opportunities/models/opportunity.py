"""
OpportuCI - Opportunity Models
==============================
Core models for opportunities, sources, and application tracking.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
import uuid


class OpportunityCategory(models.Model):
    """Catégories d'opportunités"""

    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=120, unique=True)
    description = models.TextField(_('description'), blank=True, null=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True, null=True)
    is_active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class OpportunitySource(models.Model):
    """
    Source d'une opportunité (site web, partenaire, manuel)

    Permet de tracker d'où viennent les opportunités et
    d'automatiser l'agrégation via scraping.
    """

    class SourceType(models.TextChoices):
        WEBSITE = 'website', _('Site web (scraping)')
        PARTNER = 'partner', _('Partenaire')
        MANUAL = 'manual', _('Saisie manuelle')
        API = 'api', _('API externe')

    name = models.CharField(_('nom'), max_length=200)
    source_type = models.CharField(
        _('type'),
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.MANUAL
    )
    url = models.URLField(_('URL'), blank=True, null=True)
    logo = models.ImageField(_('logo'), upload_to='sources/', blank=True, null=True)

    # Config scraping (si applicable)
    scrape_config = models.JSONField(
        _('configuration scraping'),
        default=dict,
        blank=True,
        help_text=_("Sélecteurs CSS, intervalles, etc.")
    )
    last_scraped_at = models.DateTimeField(_('dernier scraping'), blank=True, null=True)

    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('source')
        verbose_name_plural = _('sources')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class Opportunity(models.Model):
    """
    Modèle principal pour les opportunités

    Représente une bourse, un stage, un emploi, une formation, etc.
    Enrichi avec des champs pour le matching IA.
    """

    class OpportunityType(models.TextChoices):
        SCHOLARSHIP = 'scholarship', _('Bourse')
        INTERNSHIP = 'internship', _('Stage')
        JOB = 'job', _('Emploi')
        TRAINING = 'training', _('Formation')
        COMPETITION = 'competition', _('Concours')
        EVENT = 'event', _('Événement')
        OTHER = 'other', _('Autre')

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        PUBLISHED = 'published', _('Publiée')
        CLOSED = 'closed', _('Clôturée')
        EXPIRED = 'expired', _('Expirée')

    class EducationLevel(models.TextChoices):
        ANY = 'any', _('Tous niveaux')
        BAC = 'bac', _('Baccalauréat')
        BTS = 'bts', _('BTS/DUT')
        LICENSE = 'license', _('Licence')
        MASTER = 'master', _('Master')
        PHD = 'phd', _('Doctorat')

    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('titre'), max_length=255, db_index=True)
    slug = models.SlugField(_('slug'), max_length=280, unique=True)
    description = models.TextField(_('description'))

    # Classification
    category = models.ForeignKey(
        OpportunityCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opportunities',
        verbose_name=_('catégorie')
    )
    opportunity_type = models.CharField(
        _('type'),
        max_length=20,
        choices=OpportunityType.choices,
        db_index=True
    )

    # Organisation
    organization = models.CharField(_('organisme'), max_length=255)
    organization_logo = models.ImageField(
        _('logo organisme'),
        upload_to='organizations/',
        blank=True,
        null=True
    )
    website = models.URLField(_('site web'), blank=True, null=True)
    application_link = models.URLField(_('lien de candidature'), blank=True, null=True)
    contact_email = models.EmailField(_('email de contact'), blank=True, null=True)

    # Localisation
    location = models.CharField(_('lieu'), max_length=255, blank=True, null=True)
    is_remote = models.BooleanField(_('à distance'), default=False)

    # Dates
    publication_date = models.DateTimeField(_('date de publication'), blank=True, null=True)
    deadline = models.DateTimeField(_('date limite'), blank=True, null=True, db_index=True)
    start_date = models.DateField(_('date de début'), blank=True, null=True)

    # Exigences (pour matching IA)
    education_level = models.CharField(
        _('niveau requis'),
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.ANY
    )
    skills_required = models.JSONField(
        _('compétences requises'),
        default=list,
        blank=True,
        help_text=_("Liste de compétences: ['Python', 'Excel', ...]")
    )
    experience_years = models.PositiveIntegerField(
        _('années d\'expérience'),
        default=0,
        help_text=_("0 = débutant accepté")
    )
    requirements = models.TextField(_('autres prérequis'), blank=True, null=True)

    # Financier
    compensation = models.CharField(_('rémunération/montant'), max_length=255, blank=True, null=True)
    currency = models.CharField(_('devise'), max_length=10, default='XOF')

    # Source & Tracking
    source = models.ForeignKey(
        OpportunitySource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities',
        verbose_name=_('source')
    )
    external_id = models.CharField(
        _('ID externe'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("ID dans le système source (pour éviter les doublons)")
    )

    # Statut
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    featured = models.BooleanField(_('mise en avant'), default=False)

    # Stats
    view_count = models.PositiveIntegerField(_('vues'), default=0)

    # Métadonnées
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_opportunities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('opportunité')
        verbose_name_plural = _('opportunités')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'deadline']),
            models.Index(fields=['opportunity_type', 'status']),
            models.Index(fields=['source', 'external_id']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:250]
            unique_slug = base_slug
            counter = 1
            while Opportunity.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.deadline:
            return self.deadline < timezone.now()
        return False

    @property
    def days_until_deadline(self):
        if self.deadline:
            delta = self.deadline - timezone.now()
            return max(0, delta.days)
        return None

    def get_matching_data(self) -> dict:
        """
        Retourne les données structurées pour le matching IA.
        """
        return {
            'id': str(self.id),
            'title': self.title,
            'organization': self.organization,
            'category': self.category.name if self.category else None,
            'type': self.opportunity_type,
            'location': self.location,
            'is_remote': self.is_remote,
            'education_level': self.education_level,
            'skills_required': self.skills_required or [],
            'experience_years': self.experience_years,
            'description': self.description[:500],
        }


class ApplicationTracker(models.Model):
    """
    Suivi des candidatures utilisateur

    Remplace UserOpportunity avec un tracking plus complet
    du parcours de candidature.
    """

    class Status(models.TextChoices):
        DISCOVERED = 'discovered', _('Découverte')
        SAVED = 'saved', _('Sauvegardée')
        PREPARING = 'preparing', _('En préparation')
        APPLIED = 'applied', _('Candidature envoyée')
        INTERVIEWING = 'interviewing', _('En entretien')
        OFFER = 'offer', _('Offre reçue')
        ACCEPTED = 'accepted', _('Acceptée')
        REJECTED = 'rejected', _('Refusée')
        WITHDRAWN = 'withdrawn', _('Retirée')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    # Statut
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.DISCOVERED,
        db_index=True
    )

    # Score IA
    ai_match_score = models.FloatField(
        _('score de matching'),
        null=True,
        blank=True,
        help_text=_("Score 0-100 calculé par l'IA")
    )
    ai_match_reasons = models.JSONField(
        _('raisons du matching'),
        default=list,
        blank=True
    )

    # Dates
    discovered_at = models.DateTimeField(auto_now_add=True)
    saved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    status_updated_at = models.DateTimeField(auto_now=True)

    # Notes & Suivi
    notes = models.TextField(_('notes personnelles'), blank=True, null=True)
    next_action = models.CharField(_('prochaine action'), max_length=255, blank=True, null=True)
    next_action_date = models.DateField(_('date prochaine action'), blank=True, null=True)

    # Documents utilisés
    cv_used = models.FileField(
        _('CV utilisé'),
        upload_to='applications/cv/',
        blank=True,
        null=True
    )
    cover_letter = models.FileField(
        _('lettre de motivation'),
        upload_to='applications/letters/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('candidature')
        verbose_name_plural = _('candidatures')
        unique_together = ['user', 'opportunity']
        ordering = ['-discovered_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['opportunity', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.opportunity.title}"

    def save(self, *args, **kwargs):
        # Auto-update timestamps based on status
        now = timezone.now()
        if self.status == self.Status.SAVED and not self.saved_at:
            self.saved_at = now
        elif self.status == self.Status.APPLIED and not self.applied_at:
            self.applied_at = now
        super().save(*args, **kwargs)

    def update_status(self, new_status: str, notes: str = None):
        """Helper pour mettre à jour le statut avec historique."""
        self.status = new_status
        if notes:
            existing = self.notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            self.notes = f"{existing}\n[{timestamp}] {new_status}: {notes}".strip()
        self.save()


# Backward compatibility alias
UserOpportunity = ApplicationTracker
