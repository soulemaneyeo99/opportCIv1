"""
OpportuCI - Personalized Learning Journey
==========================================
Parcours d'apprentissage générés automatiquement par IA
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class PersonalizedLearningJourney(models.Model):
    """
    Parcours d'apprentissage personnalisé pour atteindre une opportunité
    Généré automatiquement basé sur l'analyse IA et le profil utilisateur
    """
    
    STATUS_CHOICES = [
        ('not_started', _('Pas commencé')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('paused', _('En pause')),
        ('abandoned', _('Abandonné')),
    ]
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_journeys',
        verbose_name=_('utilisateur')
    )
    
    target_opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.CASCADE,
        related_name='learning_journeys',
        verbose_name=_('opportunité cible')
    )
    
    # État du parcours
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name=_('statut')
    )
    
    # Analyse personnalisée
    user_current_level = models.JSONField(
        default=dict,
        verbose_name=_('niveau actuel utilisateur'),
        help_text=_('Format: {"Python": 0.7, "Communication": 0.5, ...}')
    )
    
    skill_gaps = models.JSONField(
        default=list,
        verbose_name=_('écarts de compétences'),
        help_text=_('Liste des compétences à développer avec priorités')
    )
    
    # Modules du parcours
    learning_modules = models.ManyToManyField(
        'MicroLearningModule',
        through='JourneyModule',
        related_name='journeys',
        verbose_name=_('modules d\'apprentissage')
    )
    
    # Métriques de progression
    total_estimated_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('heures totales estimées')
    )
    
    hours_completed = models.FloatField(
        default=0.0,
        verbose_name=_('heures complétées')
    )
    
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('pourcentage de progression')
    )
    
    modules_completed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('modules complétés')
    )
    
    # Prédictions IA
    success_probability = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_('probabilité de succès'),
        help_text=_('Estimation IA de réussite pour l\'opportunité')
    )
    
    estimated_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('date de complétion estimée')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('créé le')
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('commencé le')
    )
    
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('dernière activité')
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('complété le')
    )
    
    class Meta:
        app_label = 'learning'
        verbose_name = _('parcours d\'apprentissage')
        verbose_name_plural = _('parcours d\'apprentissage')
        unique_together = ['user', 'target_opportunity']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} → {self.target_opportunity.title}"
    
    def generate_personalized_path(self):
        """
        Génère le parcours optimal avec l'IA
        """
        from apps.ai.services.gemini_service import GeminiService
        from apps.learning.services.path_generator import PathGeneratorService
        
        try:
            # 1. Récupérer l'intelligence de l'opportunité
            try:
                opp_intelligence = self.target_opportunity.intelligence
            except:
                # Créer et analyser si pas encore fait
                from apps.learning.models import OpportunityIntelligence
                opp_intelligence = OpportunityIntelligence.objects.create(
                    opportunity=self.target_opportunity
                )
                opp_intelligence.analyze_with_ai()
            
            # 2. Évaluer niveau actuel utilisateur
            self.user_current_level = self._assess_user_skills()
            
            # 3. Identifier les gaps
            self.skill_gaps = opp_intelligence.get_skill_gaps_for_user(self.user)
            
            # 4. Générer parcours avec IA
            path_generator = PathGeneratorService()
            path_data = path_generator.generate_optimal_path(
                user=self.user,
                opportunity=self.target_opportunity,
                skill_gaps=self.skill_gaps,
                user_level=self.user_current_level
            )
            
            if not path_data:
                logger.error(f"Échec génération parcours pour journey {self.id}")
                return False
            
            # 5. Créer les modules du parcours
            self._create_journey_modules(path_data['modules'])
            
            # 6. Calculer métriques
            self.total_estimated_hours = path_data['estimated_total_hours']
            self.success_probability = opp_intelligence.estimate_success_probability(self.user)
            self.estimated_completion_date = self._calculate_completion_date()
            
            self.save()
            
            # 7. Notification utilisateur
            self._send_welcome_notification(path_data)
            
            logger.info(f"Parcours généré avec succès pour journey {self.id}")
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur génération parcours: {str(e)}",
                exc_info=True,
                extra={'journey_id': self.id}
            )
            return False
    
    def _assess_user_skills(self):
        """
        Évalue les compétences actuelles de l'utilisateur
        """
        skills = {}
        
        # Depuis le profil déclaré
        if hasattr(self.user, 'profile') and self.user.profile.skills:
            declared_skills = self.user.profile.get_skills_list()
            for skill in declared_skills:
                skills[skill] = 0.5  # Niveau moyen par défaut
        
        # Depuis les cours complétés
        from apps.learning.models import UserModuleProgress
        completed_modules = UserModuleProgress.objects.filter(
            user=self.user,
            status='completed'
        ).select_related('module')
        
        for progress in completed_modules:
            skill = progress.module.skill_taught
            # Augmenter le niveau selon le score
            if progress.best_score:
                skill_level = min(progress.best_score / 100, 1.0)
                skills[skill] = max(skills.get(skill, 0), skill_level)
        
        # Depuis les évaluations
        # TODO: Intégrer quand système d'évaluation sera implémenté
        
        return skills
    
    def _create_journey_modules(self, modules_data):
        """
        Crée les modules du parcours avec leur ordre
        """
        from apps.learning.models import MicroLearningModule, JourneyModule
        
        for idx, module_info in enumerate(modules_data, start=1):
            # Trouver ou créer le module
            module = MicroLearningModule.objects.filter(
                skill_taught=module_info['skill'],
                difficulty_level=module_info.get('difficulty', 'intermediate')
            ).first()
            
            if not module:
                # Créer un placeholder (sera rempli par content team)
                module = MicroLearningModule.objects.create(
                    title=module_info['title'],
                    skill_taught=module_info['skill'],
                    content_type=module_info.get('type', 'video'),
                    difficulty_level=module_info.get('difficulty', 'intermediate'),
                    duration_minutes=module_info.get('duration_minutes', 15),
                    is_active=False,  # Pas encore prêt
                )
            
            # Lier au parcours
            JourneyModule.objects.create(
                journey=self,
                module=module,
                order=idx,
                priority=module_info.get('priority', 'medium'),
                is_mandatory=module_info.get('priority') in ['critical', 'high']
            )
    
    def _calculate_completion_date(self):
        """
        Estime la date de complétion
        """
        # Hypothèse: 2h d'étude par jour en moyenne
        daily_hours = 2
        days_needed = self.total_estimated_hours / daily_hours
        
        # Ajouter 20% buffer pour imprévus
        days_needed = int(days_needed * 1.2)
        
        return timezone.now().date() + timedelta(days=days_needed)
    
    def _send_welcome_notification(self, path_data):
        """
        Envoie notification de bienvenue
        """
        from apps.notifications.services import NotificationService
        
        message = f"""
        🎯 Ton parcours personnalisé est prêt !
        
        Objectif : {self.target_opportunity.title}
        Durée estimée : {self.total_estimated_hours}h
        Modules : {len(path_data['modules'])}
        Probabilité de succès : {int(self.success_probability * 100)}%
        
        Premier module : {path_data['modules'][0]['title']}
        
        C'est parti ! 🚀
        """
        
        NotificationService.create_notification(
            user=self.user,
            title="Ton parcours d'apprentissage est prêt !",
            message=message.strip(),
            notification_type='system',
            related_object=self
        )
    
    def start_journey(self):
        """
        Démarre le parcours
        """
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.last_activity = timezone.now()
            self.save()
            
            logger.info(f"Journey {self.id} démarré par user {self.user.id}")
    
    def update_progress(self):
        """
        Met à jour la progression globale
        """
        journey_modules = self.journey_modules.all()
        
        if not journey_modules.exists():
            return
        
        # Calculer progression
        total_modules = journey_modules.count()
        completed_modules = journey_modules.filter(completed=True).count()
        
        self.modules_completed = completed_modules
        self.progress_percentage = int((completed_modules / total_modules) * 100)
        
        # Heures complétées
        total_time = journey_modules.aggregate(
            models.Sum('time_spent_minutes')
        )['time_spent_minutes__sum'] or 0
        self.hours_completed = total_time / 60
        
        # Mettre à jour statut
        if self.progress_percentage == 100 and self.status != 'completed':
            self.complete_journey()
        
        self.last_activity = timezone.now()
        self.save()
    
    def complete_journey(self):
        """
        Marque le parcours comme complété
        """
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()
        
        # Récompenses
        self._award_completion_rewards()
        
        # Notification
        from apps.notifications.services import NotificationService
        NotificationService.create_notification(
            user=self.user,
            title="Parcours terminé ! 🎉",
            message=f"Félicitations ! Tu as complété le parcours pour {self.target_opportunity.title}. Tu es maintenant prêt à candidater !",
            notification_type='achievement',
            related_object=self
        )
        
        logger.info(f"Journey {self.id} complété par user {self.user.id}")
    
    def _award_completion_rewards(self):
        """
        Attribue les récompenses de complétion
        """
        from apps.credibility.models import CredibilityPoints, PointsHistory
        
        # Points basés sur durée et difficulté
        base_points = self.total_estimated_hours * 10
        difficulty_multiplier = {
            'not_started': 1.0,
            'in_progress': 1.0,
            'completed': 1.5,  # Bonus complétion
        }.get(self.status, 1.0)
        
        total_points = int(base_points * difficulty_multiplier)
        
        # Attribuer points
        cred, _ = CredibilityPoints.objects.get_or_create(user=self.user)
        cred.add_points(total_points)
        
        PointsHistory.objects.create(
            user=self.user,
            operation='add',
            points=total_points,
            source='course_completion',
            description=f"Parcours complété : {self.target_opportunity.title}"
        )


class JourneyModule(models.Model):
    """
    Relation entre parcours et modules avec métadonnées
    """
    
    journey = models.ForeignKey(
        PersonalizedLearningJourney,
        on_delete=models.CASCADE,
        related_name='journey_modules',
        verbose_name=_('parcours')
    )
    
    module = models.ForeignKey(
        'MicroLearningModule',
        on_delete=models.CASCADE,
        related_name='journey_assignments',
        verbose_name=_('module')
    )
    
    order = models.PositiveIntegerField(
        verbose_name=_('ordre')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('critical', _('Critique')),
            ('high', _('Haute')),
            ('medium', _('Moyenne')),
            ('low', _('Basse')),
        ],
        default='medium',
        verbose_name=_('priorité')
    )
    
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('obligatoire')
    )
    
    # Progression
    started = models.BooleanField(
        default=False,
        verbose_name=_('commencé')
    )
    
    completed = models.BooleanField(
        default=False,
        verbose_name=_('complété')
    )
    
    time_spent_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('temps passé (minutes)')
    )
    
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name=_('tentatives')
    )
    
    best_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_('meilleur score')
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('commencé le')
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('complété le')
    )
    
    class Meta:
        app_label = 'learning'
        verbose_name = _('module de parcours')
        verbose_name_plural = _('modules de parcours')
        ordering = ['order']
        unique_together = ['journey', 'module']
    
    def __str__(self):
        return f"{self.journey.user.username} - {self.module.title} (#{self.order})"
    
    def mark_completed(self, score=None):
        """
        Marque le module comme complété
        """
        self.completed = True
        self.completed_at = timezone.now()
        
        if score is not None:
            self.best_score = max(self.best_score or 0, score)
        
        self.save()
        
        # Mettre à jour le parcours parent
        self.journey.update_progress()
        
        # Notification si module critique
        if self.priority == 'critical':
            from apps.notifications.services import NotificationService
            NotificationService.create_notification(
                user=self.journey.user,
                title="Module critique complété ! 🎉",
                message=f"Bravo ! Tu as terminé {self.module.title}. Tu te rapproches de ton objectif !",
                notification_type='achievement'
            )