"""
OpportuCI - User & Profile Models
=================================
Modèles utilisateur simplifiés pour MVP
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import FileExtensionValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_file_size(file_obj):
    """Valide la taille du fichier (max 5MB)"""
    max_size = 5 * 1024 * 1024
    if file_obj.size > max_size:
        raise ValidationError(_('La taille maximale du fichier est de 5MB'))


def profile_picture_path(instance, filename):
    """Chemin de stockage pour les photos de profil"""
    ext = filename.split('.')[-1].lower()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'users/{instance.id}/profile_{timestamp}.{ext}'


def cv_upload_path(instance, filename):
    """Chemin de stockage pour les CV"""
    ext = filename.split('.')[-1].lower()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'users/{instance.user.id}/cv_{timestamp}.{ext}'


class CustomUserManager(BaseUserManager):
    """Gestionnaire personnalisé - email comme identifiant unique"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('L\'adresse e-mail est obligatoire'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modèle utilisateur OpportuCI

    Simplifié pour MVP - focus sur l'essentiel pour l'auth et le matching.
    """

    class UserType(models.TextChoices):
        STUDENT = 'student', _('Étudiant')
        PROFESSIONAL = 'professional', _('Professionnel')
        ORGANIZATION = 'organization', _('Organisation')
        ADMIN = 'admin', _('Administrateur')

    # Remove username requirement - use email only
    username = models.CharField(max_length=150, blank=True, null=True)

    email = models.EmailField(
        _('adresse e-mail'),
        unique=True,
        db_index=True,
        error_messages={'unique': _("Un utilisateur avec cette adresse e-mail existe déjà.")}
    )

    user_type = models.CharField(
        _('type d\'utilisateur'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.STUDENT,
        db_index=True
    )

    phone_number = models.CharField(
        _('numéro de téléphone'),
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?225[0-9]{8,10}$',
                message=_("Numéro ivoirien valide requis (ex: +2250102030405)")
            )
        ]
    )

    profile_picture = models.ImageField(
        _('photo de profil'),
        upload_to=profile_picture_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ]
    )

    is_verified = models.BooleanField(_('email vérifié'), default=False)

    created_at = models.DateTimeField(_('date de création'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email.split('@')[0]


class Profile(models.Model):
    """
    Profil utilisateur pour OpportuCI

    Contient toutes les infos pour le matching IA avec les opportunités.
    """

    class EducationLevel(models.TextChoices):
        SECONDARY = 'secondary', _('Secondaire')
        BAC = 'bac', _('Baccalauréat')
        BTS = 'bts', _('BTS/DUT')
        LICENSE = 'license', _('Licence')
        MASTER = 'master', _('Master')
        PHD = 'phd', _('Doctorat')
        OTHER = 'other', _('Autre')

    class City(models.TextChoices):
        ABIDJAN = 'abidjan', _('Abidjan')
        BOUAKE = 'bouake', _('Bouaké')
        DALOA = 'daloa', _('Daloa')
        YAMOUSSOUKRO = 'yamoussoukro', _('Yamoussoukro')
        SAN_PEDRO = 'san_pedro', _('San-Pédro')
        KORHOGO = 'korhogo', _('Korhogo')
        MAN = 'man', _('Man')
        OTHER = 'other', _('Autre ville')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('utilisateur')
    )

    # Localisation
    city = models.CharField(
        _('ville'),
        max_length=50,
        choices=City.choices,
        default=City.ABIDJAN
    )

    # Éducation
    education_level = models.CharField(
        _('niveau d\'éducation'),
        max_length=20,
        choices=EducationLevel.choices,
        blank=True,
        null=True
    )
    field_of_study = models.CharField(
        _('domaine d\'étude'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_("Ex: Informatique, Gestion, Médecine...")
    )
    institution = models.CharField(
        _('établissement'),
        max_length=200,
        blank=True,
        null=True
    )
    graduation_year = models.PositiveIntegerField(
        _('année de graduation'),
        blank=True,
        null=True
    )

    # Compétences & Intérêts (JSONField pour matching IA)
    skills = models.JSONField(
        _('compétences'),
        default=list,
        blank=True,
        help_text=_("Liste de compétences: ['Python', 'Excel', 'Communication']")
    )
    interests = models.JSONField(
        _('centres d\'intérêt'),
        default=list,
        blank=True,
        help_text=_("Domaines d'intérêt: ['Tech', 'Finance', 'Santé']")
    )
    languages = models.JSONField(
        _('langues'),
        default=list,
        blank=True,
        help_text=_("Langues parlées: ['Français', 'Anglais']")
    )

    # Documents
    cv = models.FileField(
        _('CV'),
        upload_to=cv_upload_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size
        ]
    )

    # Liens professionnels
    linkedin_url = models.URLField(_('LinkedIn'), blank=True, null=True)
    portfolio_url = models.URLField(_('Portfolio'), blank=True, null=True)

    # Bio
    bio = models.TextField(
        _('biographie'),
        blank=True,
        null=True,
        help_text=_("Décrivez vos objectifs professionnels")
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('profil')
        verbose_name_plural = _('profils')

    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"

    def get_matching_data(self) -> dict:
        """
        Retourne les données structurées pour le matching IA.
        Utilisé par GeminiAIService.get_opportunity_recommendations()
        """
        return {
            'name': self.user.get_full_name(),
            'education_level': self.education_level,
            'field_of_study': self.field_of_study,
            'institution': self.institution,
            'skills': self.skills or [],
            'interests': self.interests or [],
            'languages': self.languages or [],
            'location': self.city,
            'user_type': self.user.user_type,
        }


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil lors de la création d'un utilisateur."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil quand l'utilisateur est sauvegardé."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
