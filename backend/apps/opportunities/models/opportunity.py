# opportunities/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import uuid

class OpportunityCategory(models.Model):
    """Catégories d'opportunités"""
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=120, unique=True)
    description = models.TextField(_('description'), blank=True, null=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True, null=True)
    is_active = models.BooleanField(_('est actif'), default=True)
    
    class Meta:
        verbose_name = _('catégorie d\'opportunité')
        verbose_name_plural = _('catégories d\'opportunités')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Opportunity(models.Model):
    """Modèle principal pour les opportunités"""
    # Types d'opportunités
    TYPE_CHOICES = (
        ('scholarship', _('Bourse')),
        ('internship', _('Stage')),
        ('job', _('Emploi')),
        ('competition', _('Concours')),
        ('training', _('Formation')),
        ('event', _('Événement')),
        ('other', _('Autre')),
    )
    
    # Statuts d'opportunité
    STATUS_CHOICES = (
        ('draft', _('Brouillon')),
        ('published', _('Publiée')),
        ('closed', _('Clôturée')),
        ('expired', _('Expirée')),
    )
    
    # Champs de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=280, unique=True)
    description = models.TextField(_('description'))
    
    # Classification
    category = models.ForeignKey(OpportunityCategory, on_delete=models.SET_NULL, 
                                null=True, related_name='opportunities')
    opportunity_type = models.CharField(_('type d\'opportunité'), max_length=20, choices=TYPE_CHOICES)
    
    # Dates importantes
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    publication_date = models.DateTimeField(_('date de publication'), blank=True, null=True)
    deadline = models.DateTimeField(_('date limite'), blank=True, null=True)
    
    # Détails
    location = models.CharField(_('lieu'), max_length=255, blank=True, null=True)
    is_remote = models.BooleanField(_('à distance'), default=False)
    organization = models.CharField(_('organisme/entreprise'), max_length=255)
    website = models.URLField(_('site web'), blank=True, null=True)
    application_link = models.URLField(_('lien de candidature'), blank=True, null=True)
    contact_email = models.EmailField(_('email de contact'), blank=True, null=True)
    
    # Exigences
    requirements = models.TextField(_('prérequis'), blank=True, null=True)
    education_level = models.CharField(_('niveau d\'éducation requis'), max_length=100, blank=True, null=True)
    
    # Détails financiers (pour bourses, emplois)
    compensation = models.CharField(_('rémunération/montant'), max_length=255, blank=True, null=True)
    currency = models.CharField(_('devise'), max_length=10, default='XOF')
    
    # Métadonnées
    tags = models.CharField(_('tags'), max_length=500, blank=True, null=True)
    featured = models.BooleanField(_('mise en avant'), default=False)
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Relations
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='created_opportunities')
    
    # Pour le suivi des statistiques
    view_count = models.PositiveIntegerField(_('nombre de vues'), default=0)
    application_count = models.PositiveIntegerField(_('nombre de candidatures'), default=0)
    
    class Meta:
        verbose_name = _('opportunité')
        verbose_name_plural = _('opportunités')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Générer un slug unique lors de la sauvegarde"""
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            counter = 1
            
            while Opportunity.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
                
            self.slug = unique_slug
            
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Vérifier si l'opportunité est expirée"""
        from django.utils import timezone
        if self.deadline:
            return self.deadline < timezone.now()
        return False
    
    def update_status(self):
        """Mettre à jour le statut en fonction de la date d'expiration"""
        if self.is_expired and self.status == 'published':
            self.status = 'expired'
            self.save(update_fields=['status'])

class UserOpportunity(models.Model):
    """Relation entre utilisateurs et opportunités"""
    # Types de relations
    RELATION_CHOICES = (
        ('saved', _('Sauvegardée')),
        ('applied', _('Postulée')),
        ('viewed', _('Consultée')),
        ('shared', _('Partagée')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='user_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, 
                                   related_name='user_relations')
    relation_type = models.CharField(_('type de relation'), max_length=20, choices=RELATION_CHOICES)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    notes = models.TextField(_('notes'), blank=True, null=True)
    status = models.CharField(_('statut'), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('opportunité utilisateur')
        verbose_name_plural = _('opportunités utilisateur')
        unique_together = ('user', 'opportunity', 'relation_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title} ({self.get_relation_type_display()})"