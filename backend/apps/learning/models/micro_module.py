"""
OpportuCI - Micro Learning Module Model
========================================
Modules d'apprentissage de 5-15 minutes optimisés 4G/5G
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class MicroLearningModule(models.Model):
    """
    Module d'apprentissage ultra-ciblé
    Durée : 5-15 minutes
    Optimisé pour connexion 4G/5G mobile
    """
    
    CONTENT_TYPES = [
        ('video', 'Vidéo tutoriel'),
        ('interactive', 'Exercice interactif'),
        ('quiz', 'Quiz évaluation'),
        ('reading', 'Lecture guidée'),
        ('project', 'Projet pratique'),
        ('simulation', 'Simulation professionnelle'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]
    
    NETWORK_QUALITIES = [
        ('480p', '480p - 4G optimisé'),
        ('720p', '720p - 5G/WiFi'),
        ('1080p', '1080p - WiFi uniquement'),
    ]
    
    # Identification
    title = models.CharField('Titre', max_length=200)
    slug = models.SlugField('Slug', unique=True, blank=True)
    skill_taught = models.CharField('Compétence enseignée', max_length=100, db_index=True)
    description = models.TextField('Description')
    
    # Type et contenu
    content_type = models.CharField('Type de contenu', max_length=20, choices=CONTENT_TYPES)
    content_data = models.JSONField(
        'Données du contenu',
        default=dict,
        help_text="Structure JSON selon le type de contenu"
    )
    
    # Métadonnées pédagogiques
    duration_minutes = models.IntegerField(
        'Durée (minutes)',
        validators=[MinValueValidator(5), MaxValueValidator(30)]
    )
    difficulty_level = models.CharField(
        'Niveau de difficulté',
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='intermediate'
    )
    learning_objectives = models.JSONField(
        'Objectifs d\'apprentissage',
        default=list,
        help_text="Liste des objectifs pédagogiques"
    )
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='unlocks',
        verbose_name='Prérequis'
    )
    
    # Optimisation réseau (crucial pour CI)
    video_480p_url = models.URLField('Vidéo 480p (4G)', blank=True, null=True)
    video_720p_url = models.URLField('Vidéo 720p (5G)', blank=True, null=True)
    video_1080p_url = models.URLField('Vidéo 1080p (WiFi)', blank=True, null=True)
    estimated_data_mb = models.IntegerField(
        'Data estimée (MB)',
        default=10,
        help_text="Consommation data moyenne"
    )
    offline_capable = models.BooleanField(
        'Disponible hors-ligne',
        default=False,
        help_text="Le module peut être téléchargé pour usage offline"
    )
    
    # Contextualisation locale
    local_examples = models.BooleanField(
        'Exemples locaux',
        default=True,
        help_text="Utilise des exemples ivoiriens/africains"
    )
    local_context_description = models.TextField(
        'Description contexte local',
        blank=True,
        help_text="Ex: Cas pratique avec une entreprise ivoirienne"
    )
    language = models.CharField('Langue', max_length=5, default='fr')
    uses_ivorian_scenarios = models.BooleanField(
        'Scénarios ivoiriens',
        default=True
    )
    
    # Gamification
    points_reward = models.IntegerField(
        'Points récompense',
        default=10,
        validators=[MinValueValidator(0)]
    )
    badge_unlocked = models.ForeignKey(
        'credibility.Badge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Badge débloqué',
        help_text="Badge obtenu après complétion"
    )
    
    # Métriques d'usage
    total_completions = models.IntegerField('Complétions totales', default=0)
    average_score = models.FloatField('Score moyen', default=0.0)
    average_time_minutes = models.IntegerField('Temps moyen (min)', default=0)
    success_rate = models.FloatField(
        'Taux de réussite',
        default=0.0,
        help_text="% d'utilisateurs ayant réussi (>70%)"
    )
    
    # Gestion
    is_active = models.BooleanField('Actif', default=True, db_index=True)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_modules',
        verbose_name='Créé par'
    )
    
    class Meta:
        app_label = 'learning'
        verbose_name = "Module Micro-Learning"
        verbose_name_plural = "Modules Micro-Learning"
        ordering = ['skill_taught', 'difficulty_level', 'order_in_skill']
        indexes = [
            models.Index(fields=['skill_taught', 'difficulty_level']),
            models.Index(fields=['content_type', 'is_active']),
            models.Index(fields=['is_active', '-total_completions']),
        ]
    
    # Ordre dans la compétence
    order_in_skill = models.PositiveIntegerField(
        'Ordre dans compétence',
        default=0,
        help_text="Ordre recommandé d'apprentissage"
    )
    
    def __str__(self):
        return f"{self.title} ({self.skill_taught})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Assurer unicité
            counter = 1
            original_slug = self.slug
            while MicroLearningModule.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validation du modèle"""
        super().clean()
        
        # Validation durée selon type
        if self.content_type == 'project' and self.duration_minutes < 15:
            raise ValidationError({
                'duration_minutes': 'Un projet doit durer au moins 15 minutes'
            })
        
        # Validation vidéos
        if self.content_type == 'video':
            if not any([self.video_480p_url, self.video_720p_url, self.video_1080p_url]):
                raise ValidationError({
                    'content_type': 'Au moins une qualité vidéo doit être fournie'
                })
    
    def get_adaptive_content(self, network_type='4G', user_preference=None):
        """
        Retourne le contenu adapté au type de réseau
        
        Args:
            network_type: '3G', '4G', '5G', 'WiFi'
            user_preference: Préférence utilisateur (économie data, etc.)
            
        Returns:
            Dict avec le contenu optimisé
        """
        # Mode économie data forcé
        if user_preference == 'data_saver':
            if self.content_type == 'video':
                return {
                    'type': 'text_alternative',
                    'content': self.content_data.get('transcript', ''),
                    'slides': self.content_data.get('key_slides', []),
                    'estimated_data_mb': 1
                }
        
        # Adaptation selon réseau
        if self.content_type == 'video':
            if network_type in ['2G', '3G']:
                # Texte uniquement pour 2G/3G
                return {
                    'type': 'text',
                    'url': None,
                    'content': self.content_data.get('transcript', 'Transcript non disponible'),
                    'estimated_data_mb': 0.5
                }
            elif network_type == '4G':
                return {
                    'type': 'video',
                    'url': self.video_480p_url or self.video_720p_url,
                    'quality': '480p',
                    'estimated_data_mb': self.estimated_data_mb * 0.6
                }
            elif network_type in ['5G', 'WiFi']:
                return {
                    'type': 'video',
                    'url': self.video_720p_url or self.video_1080p_url or self.video_480p_url,
                    'quality': '720p',
                    'estimated_data_mb': self.estimated_data_mb
                }
        
        # Autres types de contenu
        return {
            'type': self.content_type,
            'content': self.content_data,
            'estimated_data_mb': self.estimated_data_mb
        }
    
    def update_metrics(self, completion_time_minutes, score=None):
        """
        Met à jour les métriques après une complétion
        
        Args:
            completion_time_minutes: Temps pris par l'utilisateur
            score: Score obtenu (0-100) si applicable
        """
        # Incrémenter complétions
        self.total_completions += 1
        
        # Mettre à jour temps moyen
        if self.average_time_minutes == 0:
            self.average_time_minutes = completion_time_minutes
        else:
            # Moyenne pondérée
            total_time = self.average_time_minutes * (self.total_completions - 1)
            self.average_time_minutes = int((total_time + completion_time_minutes) / self.total_completions)
        
        # Mettre à jour score moyen si applicable
        if score is not None:
            if self.average_score == 0:
                self.average_score = score
            else:
                total_score = self.average_score * (self.total_completions - 1)
                self.average_score = (total_score + score) / self.total_completions
            
            # Taux de réussite (score >= 70)
            if score >= 70:
                success_count = int(self.success_rate * (self.total_completions - 1) / 100) + 1
                self.success_rate = (success_count / self.total_completions) * 100
        
        self.save(update_fields=['total_completions', 'average_time_minutes', 'average_score', 'success_rate'])
    
    @property
    def is_video(self):
        return self.content_type == 'video'
    
    @property
    def is_interactive(self):
        return self.content_type in ['interactive', 'quiz', 'project', 'simulation']
    
    @property
    def estimated_data_usage_text(self):
        """Texte lisible de la consommation data"""
        if self.estimated_data_mb < 1:
            return f"{int(self.estimated_data_mb * 1024)} KB"
        return f"{self.estimated_data_mb} MB"
    
    @classmethod
    def get_recommended_for_skill(cls, skill_name, user_level='beginner', limit=5):
        """
        Récupère les modules recommandés pour une compétence
        
        Args:
            skill_name: Nom de la compétence
            user_level: Niveau de l'utilisateur
            limit: Nombre max de modules
            
        Returns:
            QuerySet de modules triés par pertinence
        """
        modules = cls.objects.filter(
            skill_taught__icontains=skill_name,
            is_active=True,
            difficulty_level=user_level
        ).order_by('order_in_skill', '-success_rate')[:limit]
        
        return modules