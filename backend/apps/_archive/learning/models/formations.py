#apps/learning/models/formations.py

"""
OpportuCI - Formations Models
==============================
Gestion des formations et inscriptions
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Catégorie de formation"""
    
    name = models.CharField(_('nom'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True, help_text="Nom de l'icône (ex: code, design)")
    order = models.PositiveIntegerField(_('ordre'), default=0, help_text="Ordre d'affichage")
    is_active = models.BooleanField(_('active'), default=True, db_index=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_categories'
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def active_formations_count(self):
        """Nombre de formations actives dans cette catégorie"""
        return self.formations.filter(is_active=True).count()


class Formation(models.Model):
    """Formation complète avec sessions"""
    
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('upcoming', _('À venir')),
        ('ongoing', _('En cours')),
        ('completed', _('Terminée')),
        ('canceled', _('Annulée')),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', _('Débutant')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
        ('all', _('Tous niveaux')),
    ]

    # Identification
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    description = models.TextField(_('description'))
    short_description = models.CharField(
        _('description courte'),
        max_length=200,
        blank=True,
        help_text="Résumé en une phrase"
    )
    
    # Catégorisation
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='formations',
        verbose_name=_('catégorie')
    )
    
    # Contenu
    instructor = models.CharField(_('formateur'), max_length=255)
    instructor_bio = models.TextField(_('bio formateur'), blank=True)
    image = models.ImageField(
        _('image'),
        upload_to='formations/images/',
        blank=True,
        null=True
    )
    video_trailer_url = models.URLField(_('URL trailer vidéo'), blank=True)
    
    # Dates et lieu
    start_date = models.DateTimeField(_('date de début'))
    end_date = models.DateTimeField(_('date de fin'))
    location = models.CharField(_('lieu'), max_length=255, blank=True)
    is_online = models.BooleanField(_('en ligne'), default=False)
    meeting_url = models.URLField(_('URL réunion'), blank=True, help_text="Lien Zoom/Teams")
    
    # Tarification
    is_free = models.BooleanField(_('gratuit'), default=False, db_index=True)
    price_fcfa = models.PositiveIntegerField(
        _('prix (FCFA)'),
        blank=True,
        null=True,
        help_text="Prix en francs CFA"
    )
    
    # Capacité
    max_participants = models.PositiveIntegerField(
        _('participants maximum'),
        blank=True,
        null=True
    )
    
    # Métadonnées pédagogiques
    level = models.CharField(
        _('niveau'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner'
    )
    duration_hours = models.PositiveIntegerField(
        _('durée (heures)'),
        default=10
    )
    certificate_delivered = models.BooleanField(
        _('certificat délivré'),
        default=True
    )
    
    # Prérequis
    prerequisites = models.TextField(
        _('prérequis'),
        blank=True,
        help_text="Compétences requises avant de commencer"
    )
    
    # Objectifs pédagogiques
    learning_objectives = models.JSONField(
        _('objectifs pédagogiques'),
        default=list,
        blank=True,
        help_text="Liste des objectifs à atteindre"
    )
    
    # État
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    is_active = models.BooleanField(_('active'), default=True, db_index=True)
    is_featured = models.BooleanField(_('mise en avant'), default=False)
    
    # Métriques
    total_enrollments = models.PositiveIntegerField(_('inscriptions totales'), default=0)
    average_rating = models.FloatField(_('note moyenne'), default=0.0)
    completion_rate = models.FloatField(_('taux de complétion'), default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    published_at = models.DateTimeField(_('publié le'), blank=True, null=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_formations'
        verbose_name = _('formation')
        verbose_name_plural = _('formations')
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['is_free', 'is_active']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['-start_date']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Formation.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-calculer short_description si vide
        if not self.short_description and self.description:
            self.short_description = self.description[:197] + '...'
        
        super().save(*args, **kwargs)
    
    @property
    def current_participants_count(self):
        """Nombre d'inscrits actuels"""
        return self.enrollments.filter(status='approved').count()
    
    @property
    def is_full(self):
        """Formation complète?"""
        if self.max_participants:
            return self.current_participants_count >= self.max_participants
        return False
    
    @property
    def spots_remaining(self):
        """Places restantes"""
        if self.max_participants:
            return max(0, self.max_participants - self.current_participants_count)
        return None
    
    @property
    def can_enroll(self):
        """Peut-on s'inscrire?"""
        return (
            self.is_active and
            self.status in ['upcoming', 'ongoing'] and
            not self.is_full
        )


class Enrollment(models.Model):
    """Inscription d'un utilisateur à une formation"""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('canceled', _('Annulée')),
        ('completed', _('Terminée')),
    ]
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='formation_enrollments',
        verbose_name=_('utilisateur')
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('formation')
    )
    
    # État de l'inscription
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Progression
    completion_percentage = models.PositiveIntegerField(
        _('pourcentage de complétion'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    modules_completed = models.PositiveIntegerField(_('modules complétés'), default=0)
    time_spent_hours = models.FloatField(_('temps passé (heures)'), default=0.0)
    
    # Certification
    certificate_issued = models.BooleanField(_('certificat émis'), default=False)
    certificate_number = models.CharField(
        _('numéro certificat'),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )
    certificate_issued_at = models.DateTimeField(_('certificat émis le'), blank=True, null=True)
    
    # Feedback
    feedback = models.TextField(_('commentaire'), blank=True)
    rating = models.PositiveSmallIntegerField(
        _('note'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    rated_at = models.DateTimeField(_('noté le'), blank=True, null=True)
    
    # Paiement
    payment_status = models.CharField(
        _('statut paiement'),
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('completed', _('Payé')),
            ('failed', _('Échoué')),
            ('refunded', _('Remboursé')),
        ],
        default='pending'
    )
    payment_reference = models.CharField(_('référence paiement'), max_length=100, blank=True)
    
    # Timestamps
    enrollment_date = models.DateTimeField(_("date d'inscription"), auto_now_add=True)
    approved_at = models.DateTimeField(_('approuvé le'), blank=True, null=True)
    completed_at = models.DateTimeField(_('terminé le'), blank=True, null=True)
    last_accessed = models.DateTimeField(_('dernier accès'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_enrollments'
        verbose_name = _('inscription')
        verbose_name_plural = _('inscriptions')
        unique_together = [('user', 'formation')]
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['formation', 'status']),
            models.Index(fields=['status', '-enrollment_date']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.formation.title}"
    
    def approve(self):
        """Approuver l'inscription"""
        from django.utils import timezone
        
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()
        
        # Notification
        self._send_approval_notification()
    
    def complete(self):
        """Marquer comme terminée"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.completion_percentage = 100
        self.completed_at = timezone.now()
        self.save()
        
        # Générer certificat si applicable
        if self.formation.certificate_delivered and not self.certificate_issued:
            self.issue_certificate()
    
    def issue_certificate(self):
        """Émettre le certificat"""
        from django.utils import timezone
        import uuid
        
        if not self.certificate_issued:
            self.certificate_issued = True
            self.certificate_number = f"OPCI-{uuid.uuid4().hex[:8].upper()}"
            self.certificate_issued_at = timezone.now()
            self.save()
            
            # Notification
            self._send_certificate_notification()
    
    def _send_approval_notification(self):
        """Notification d'approbation"""
        from apps.notifications.services import NotificationService
        
        NotificationService.create_notification(
            user=self.user,
            title="Inscription approuvée ! 🎉",
            message=f"Ton inscription à {self.formation.title} a été approuvée. La formation commence le {self.formation.start_date.strftime('%d/%m/%Y')}.",
            notification_type='system',
            related_object=self
        )
    
    def _send_certificate_notification(self):
        """Notification de certificat"""
        from apps.notifications.services import NotificationService
        
        NotificationService.create_notification(
            user=self.user,
            title="Certificat disponible ! 🏆",
            message=f"Félicitations ! Ton certificat pour {self.formation.title} est prêt. Numéro : {self.certificate_number}",
            notification_type='achievement',
            related_object=self
        )