from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import FileExtensionValidator, MinLengthValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import os

def validate_file_size(file_obj):
    """Valide la taille du fichier (max 5MB)"""
    max_size = 5 * 1024 * 1024  # 5MB
    if file_obj.size > max_size:
        raise ValidationError(_('La taille maximale du fichier est de 5MB'))

def profile_picture_upload_path(instance, filename):
    """Chemin de stockage pour les photos de profil"""
    ext = filename.split('.')[-1].lower()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'users/{instance.id}/profile_pictures/{instance.username}_{timestamp}.{ext}'

def user_cv_upload_path(instance, filename):
    """Chemin de stockage pour les CV"""
    ext = filename.split('.')[-1].lower()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'users/{instance.user.id}/cv/{instance.user.username}_{timestamp}.{ext}'

class CustomUserManager(BaseUserManager):
    """Gestionnaire personnalisé pour le modèle User avec l'email comme identifiant unique."""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('L\'adresse e-mail est obligatoire'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractUser):
    """Modèle utilisateur étendu pour OpportuCI."""

    class UserType(models.TextChoices):
        STUDENT = 'student', _('Étudiant')
        TEACHER = 'teacher', _('Enseignant')
        PROFESSIONAL = 'professional', _('Professionnel')
        ORGANIZATION = 'organization', _('Organisation')
        ADMIN = 'admin', _('Administrateur')

    class EducationLevel(models.TextChoices):
        SECONDARY = 'secondary', _('Secondaire')
        BACCALAUREATE = 'baccalaureate', _('Baccalauréat')
        BTS = 'bts', _('BTS')
        LICENSE = 'license', _('Licence')
        MASTER = 'master', _('Master')
        PHD = 'phd', _('Doctorat')
        OTHER = 'other', _('Autre')

    # Informations de base
    email = models.EmailField(
        _('adresse e-mail'), 
        unique=True, 
        db_index=True,
        error_messages={'unique': _("Un utilisateur avec cette adresse e-mail existe déjà.")}
    )
    user_type = models.CharField(  # Changé de usertype à user_type
        _('type d\'utilisateur'), 
        max_length=20, 
        choices=UserType.choices, 
        default=UserType.STUDENT,
        db_index=True
    )

    # Informations personnelles
    phone_number = models.CharField(
        _('numéro de téléphone'), 
        max_length=20,  # Changé de maxlength
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?225[0-9]{8,10}$',
                message=_("Le numéro doit être un numéro ivoirien valide (ex: +2250102030405)")
            )
        ]
    )
    profile_picture = models.ImageField(
        _('photo de profil'), 
        upload_to=profile_picture_upload_path, 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size  # Correction du nom de la fonction
        ]
    )
    CITY_CHOICES = [
        ('abidjan', 'Abidjan'),
        ('bouake', 'Bouaké'),
        ('daloa', 'Daloa'),
        ('yamoussoukro', 'Yamoussoukro'),
        ('sanpedro', 'San-Pédro'),
        ('korhogo', 'Korhogo'),
        ('man', 'Man'),
        ('other', 'Autre ville'),
    ]

    city = models.CharField(
        _('ville'),
        max_length=100,
        blank=True,
        null=True,
        choices=CITY_CHOICES,
        default='abidjan'  # Valeur par défaut optionnelle
    )
    
    country = models.CharField(
        _('pays'), 
        max_length=100, 
        default='Côte d\'Ivoire'
    )

    # Informations académiques (pour étudiants)
    education_level = models.CharField(  # Changé de educationlevel
        _('niveau d\'éducation'), 
        max_length=50,  # Changé de maxlength
        choices=EducationLevel.choices, 
        blank=True, 
        null=True
    )
    institution = models.CharField(
        _('établissement d\'enseignement'), 
        max_length=200, 
        blank=True, 
        null=True
    )
    field_of_study = models.CharField(  # Changé de field_ofstudy
        _('domaine d\'étude'), 
        max_length=200, 
        blank=True, 
        null=True
    )
    graduation_year = models.PositiveIntegerField(  # Changé de graduationyear
        _('année de graduation prévue'), 
        blank=True, 
        null=True
    )

    # Statut et vérification
    is_verified = models.BooleanField(  # Changé de isverified
        _('est vérifié'), 
        default=False
    )
    verification_token = models.CharField(  # Changé de verificationtoken
        _('jeton de vérification'), 
        max_length=100, 
        blank=True, 
        null=True
    )
    verification_token_expires = models.DateTimeField(  # Changé de verification_tokenexpires
        _('expiration du jeton'), 
        blank=True, 
        null=True
    )

    # Sécurité et audit
    last_login_ip = models.GenericIPAddressField(  # Changé de last_loginip
        _('dernière IP de connexion'), 
        blank=True, 
        null=True
    )
    failed_login_attempts = models.PositiveIntegerField(  # Changé de failed_loginattempts
        _('tentatives de connexion échouées'), 
        default=0
    )
    last_failed_login = models.DateTimeField(  # Changé de last_failedlogin
        _('dernière tentative échouée'), 
        blank=True, 
        null=True
    )
    is_locked = models.BooleanField(  # Changé de islocked
        _('compte verrouillé'), 
        default=False
    )

    # Métadonnées
    created_at = models.DateTimeField(  # Changé de createdat
        _('date de création'), 
        auto_now_add=True, 
        db_index=True
    )
    updated_at = models.DateTimeField(  # Changé de updatedat
        _('date de mise à jour'), 
        auto_now=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['username']),
            models.Index(fields=['city']),
            models.Index(fields=['education_level']),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def clean(self):
        """Validation personnalisée pour le modèle."""
        super().clean()

        # Validation spécifique pour les étudiants
        if self.user_type == self.UserType.STUDENT:
            if not self.education_level:
                raise ValidationError({
                    'education_level': _("Le niveau d'éducation est requis pour les étudiants")
                })
            if not self.institution:
                raise ValidationError({
                    'institution': _("L'établissement d'enseignement est requis pour les étudiants")
                })

class UserProfile(models.Model):
    """Profil utilisateur avec informations supplémentaires pour OpportuCI."""

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name=_('utilisateur')
    )
    bio = models.TextField(
        _('biographie'), 
        blank=True, 
        null=True,
        validators=[MinLengthValidator(30)],
        help_text=_("Décrivez vos objectifs académiques/professionnels (min 30 caractères)")
    )
    skills = models.TextField(
        _('compétences'), 
        blank=True, 
        null=True,
        help_text=_("Séparées par des virgules")
    )
    interests = models.TextField(
        _('centres d\'intérêt'), 
        blank=True, 
        null=True,
        help_text=_("Séparés par des virgules")
    )
    cv = models.FileField(
        _('CV'), 
        upload_to=user_cv_upload_path, 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size
        ],
        help_text=_("Formats acceptés: PDF, DOC, DOCX (max 5MB)")
    )
    linkedin_profile = models.URLField(  # Changé de linkedinprofile
        _('profil LinkedIn'), 
        blank=True, 
        null=True,
        help_text=_("Lien vers votre profil LinkedIn")
    )
    github_profile = models.URLField(  # Changé de githubprofile
        _('profil GitHub'), 
        blank=True, 
        null=True,
        help_text=_("Lien vers votre profil GitHub")
    )
    portfolio_website = models.URLField(  # Changé de portfoliowebsite
        _('site portfolio'), 
        blank=True, 
        null=True,
        help_text=_("Lien vers votre portfolio en ligne")
    )
    languages = models.TextField(
        _('langues'), 
        default='Français',
        help_text=_("Séparées par des virgules")
    )
    certifications = models.TextField(
        _('certifications'), 
        blank=True, 
        null=True,
        help_text=_("Séparées par des virgules")
    )
    availability_status = models.CharField(  # Changé de availabilitystatus
        _('statut de disponibilité'),
        max_length=50,  # Changé de maxlength
        choices=[
            ('available', _('Disponible')),
            ('limited', _('Disponibilité limitée')),
            ('unavailable', _('Non disponible')),
        ],
        default='available'
    )
    created_at = models.DateTimeField(  # Changé de createdat
        _('date de création'), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(  # Changé de updatedat
        _('date de mise à jour'), 
        auto_now=True
    )

    class Meta:
        verbose_name = _('profil utilisateur')
        verbose_name_plural = _('profils utilisateurs')
        indexes = [
            models.Index(fields=['skills']),
            models.Index(fields=['languages']),
        ]

    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"

    def get_skills_list(self):
        """Retourne les compétences sous forme de liste."""
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]

    def get_languages_list(self):
        """Retourne les langues sous forme de liste."""
        if not self.languages:
            return []
        return [lang.strip() for lang in self.languages.split(',') if lang.strip()]

    def get_certifications_list(self):
        """Retourne les certifications sous forme de liste."""
        if not self.certifications:
            return []
        return [cert.strip() for cert in self.certifications.split(',') if cert.strip()]

    def clean(self):
        """Validation personnalisée pour le profil."""
        super().clean()

        # Validation des URLs
        for field_name in ['linkedin_profile', 'github_profile', 'portfolio_website']:
            url = getattr(self, field_name)
            if url and not url.startswith(('http://', 'https://')):
                raise ValidationError({
                    field_name: _("L'URL doit commencer par http:// ou https://")
                })

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil utilisateur lors de la création d'un utilisateur."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()