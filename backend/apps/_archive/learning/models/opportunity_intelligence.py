"""
OpportuCI - Opportunity Intelligence Models
============================================
Analyse automatique des opportunités avec IA
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class OpportunityIntelligence(models.Model):
    """
    Intelligence artificielle pour analyse automatique des opportunités
    Extrait compétences, niveau, salaire estimé, etc.
    """
    
    MARKET_DEMAND_CHOICES = [
        ('very_high', _('Très demandé')),
        ('high', _('Demandé')),
        ('moderate', _('Modéré')),
        ('low', _('Faible')),
    ]
    
    # Relation avec l'opportunité
    opportunity = models.OneToOneField(
        'opportunities.Opportunity',
        on_delete=models.CASCADE,
        related_name='intelligence',
        verbose_name=_('opportunité')
    )
    
    # Compétences extraites automatiquement
    extracted_skills = models.JSONField(
        default=dict,
        verbose_name=_('compétences extraites'),
        help_text=_('Format: {"technical": [...], "soft": [...], "tools": [...], "languages": [...]}'  )
    )
    
    # Analyse de difficulté
    difficulty_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_('score de difficulté'),
        help_text=_('0 = Très facile, 1 = Très difficile')
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', _('Débutant')),
            ('intermediate', _('Intermédiaire')),
            ('advanced', _('Avancé')),
            ('expert', _('Expert')),
        ],
        default='intermediate',
        verbose_name=_('niveau de difficulté')
    )
    
    # Temps de préparation estimé
    estimated_preparation_hours = models.PositiveIntegerField(
        default=10,
        verbose_name=_('heures de préparation estimées')
    )
    
    # Contexte marché ivoirien
    typical_salary_range_fcfa = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('fourchette salariale (FCFA)'),
        help_text=_('Ex: 200000-400000')
    )
    
    market_demand = models.CharField(
        max_length=20,
        choices=MARKET_DEMAND_CHOICES,
        default='moderate',
        verbose_name=_('demande du marché')
    )
    
    growth_sectors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('secteurs en croissance'),
        help_text=_('Secteurs connexes en forte demande')
    )
    
    companies_hiring = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('entreprises qui recrutent'),
        help_text=_('Liste des entreprises similaires qui embauchent')
    )
    
    # Facteurs de succès
    success_factors = models.JSONField(
        default=list,
        verbose_name=_('facteurs de succès'),
        help_text=_('Ce qui fait réussir les candidats pour ce type de poste')
    )
    
    common_interview_questions = models.JSONField(
        default=list,
        verbose_name=_('questions d\'entretien courantes'),
        help_text=_('Questions fréquemment posées pour ce type de poste')
    )
    
    # Qualité de l'analyse
    analysis_confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_('confiance de l\'analyse'),
        help_text=_('Score de confiance de l\'IA (0-1)')
    )
    
    # Métadonnées
    analyzed_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('analysé le')
    )
    
    analysis_version = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=_('version de l\'analyse')
    )
    
    needs_reanalysis = models.BooleanField(
        default=False,
        verbose_name=_('nécessite réanalyse'),
        help_text=_('Marqué si l\'opportunité a été modifiée')
    )
    
    class Meta:
        app_label = 'learning'
        verbose_name = _('intelligence d\'opportunité')
        verbose_name_plural = _('intelligences d\'opportunités')
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['difficulty_level']),
            models.Index(fields=['market_demand']),
            models.Index(fields=['analyzed_at']),
        ]
    
    def __str__(self):
        return f"Intelligence: {self.opportunity.title}"
    
    def analyze_with_ai(self):
        """
        Lance l'analyse IA complète de l'opportunité
        Utilise Gemini pour extraction automatique
        """
        from apps.ai.services.gemini_service import GeminiService
        
        try:
            gemini = GeminiService()
            
            # Préparer les données pour l'analyse
            opportunity_data = {
                'title': self.opportunity.title,
                'type': self.opportunity.get_opportunity_type_display(),
                'organization': self.opportunity.organization,
                'description': self.opportunity.description,
                'requirements': self.opportunity.requirements or '',
                'education_level': self.opportunity.education_level or '',
                'location': self.opportunity.location or 'Côte d\'Ivoire',
            }
            
            # Appel au service Gemini
            analysis_result = gemini.analyze_opportunity_intelligence(opportunity_data)
            
            if not analysis_result:
                logger.error(f"Analyse IA échouée pour opportunité {self.opportunity.id}")
                return False
            
            # Mise à jour des champs
            self.extracted_skills = {
                'technical': analysis_result.get('technical_skills', []),
                'soft': analysis_result.get('soft_skills', []),
                'tools': analysis_result.get('tools_software', []),
                'languages': analysis_result.get('languages', ['Français']),
            }
            
            # Niveau de difficulté
            difficulty_map = {
                'beginner': (0.3, 'beginner'),
                'intermediate': (0.6, 'intermediate'),
                'advanced': (0.8, 'advanced'),
                'expert': (0.95, 'expert'),
            }
            difficulty_level = analysis_result.get('difficulty_level', 'intermediate')
            self.difficulty_score, self.difficulty_level = difficulty_map.get(
                difficulty_level, 
                (0.6, 'intermediate')
            )
            
            # Temps de préparation
            self.estimated_preparation_hours = analysis_result.get('estimated_prep_hours', 10)
            
            # Contexte marché
            market_context = analysis_result.get('market_context', {})
            self.market_demand = market_context.get('demand', 'moderate')
            self.typical_salary_range_fcfa = market_context.get('typical_salary_fcfa', '')
            self.growth_sectors = market_context.get('growth_sectors', [])
            
            # Facteurs de succès
            self.success_factors = analysis_result.get('success_factors', [])
            self.common_interview_questions = analysis_result.get('common_interview_questions', [])
            
            # Confiance
            self.analysis_confidence = analysis_result.get('confidence_score', 0.85)
            self.needs_reanalysis = False
            
            self.save()
            
            # Créer les templates de modules d'apprentissage
            self._generate_learning_templates()
            
            logger.info(f"Analyse IA réussie pour opportunité {self.opportunity.id}")
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur lors de l'analyse IA: {str(e)}", 
                exc_info=True,
                extra={'opportunity_id': self.opportunity.id}
            )
            self.analysis_confidence = 0.0
            self.save()
            return False
    
    def _generate_learning_templates(self):
        """
        Crée des templates de modules d'apprentissage
        basés sur les compétences extraites
        """
        from apps.learning.models import LearningPathTemplate
        
        all_skills = (
            self.extracted_skills.get('technical', []) +
            self.extracted_skills.get('soft', []) +
            self.extracted_skills.get('tools', [])
        )
        
        for skill in all_skills:
            # Détermine la priorité
            if skill in self.extracted_skills.get('technical', []):
                priority = 'high'
            elif skill in self.extracted_skills.get('tools', []):
                priority = 'medium'
            else:
                priority = 'low'
            
            LearningPathTemplate.objects.get_or_create(
                skill_name=skill,
                target_opportunity_type=self.opportunity.opportunity_type,
                defaults={
                    'estimated_hours': 2,
                    'difficulty': self.difficulty_score,
                    'priority': priority,
                }
            )
    
    def get_skill_gaps_for_user(self, user):
        """
        Identifie les gaps de compétences pour un utilisateur spécifique
        """
        from apps.accounts.models import UserProfile
        
        try:
            profile = UserProfile.objects.get(user=user)
            user_skills = set([
                skill.lower().strip() 
                for skill in profile.get_skills_list()
            ])
        except UserProfile.DoesNotExist:
            user_skills = set()
        
        # Comparer avec compétences requises
        gaps = []
        
        for category, skills in self.extracted_skills.items():
            for skill in skills:
                skill_normalized = skill.lower().strip()
                
                if skill_normalized not in user_skills:
                    # Calculer le gap (0-1)
                    gap_size = 0.8 if category == 'technical' else 0.6
                    
                    # Priorité basée sur catégorie
                    if category == 'technical':
                        priority = 'critical'
                    elif category == 'tools':
                        priority = 'high'
                    else:
                        priority = 'medium'
                    
                    gaps.append({
                        'skill': skill,
                        'category': category,
                        'current': 0.0,
                        'required': gap_size,
                        'gap': gap_size,
                        'priority': priority,
                    })
        
        # Trier par priorité puis par gap
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        gaps.sort(key=lambda x: (priority_order[x['priority']], -x['gap']))
        
        return gaps
    
    def estimate_success_probability(self, user):
        """
        Estime la probabilité de succès de l'utilisateur
        pour cette opportunité (0-1)
        """
        gaps = self.get_skill_gaps_for_user(user)
        
        if not gaps:
            return 0.95  # Déjà qualifié
        
        # Facteurs
        total_gaps = len(gaps)
        critical_gaps = len([g for g in gaps if g['priority'] == 'critical'])
        avg_gap = sum(g['gap'] for g in gaps) / total_gaps if total_gaps > 0 else 0
        
        # Score de base
        base_probability = 0.5
        
        # Pénalités
        gap_penalty = (critical_gaps * 0.15) + (avg_gap * 0.2)
        
        # Bonus (expérience utilisateur)
        try:
            from apps.credibility.models import CredibilityPoints
            cred = CredibilityPoints.objects.get(user=user)
            experience_bonus = min(cred.level * 0.05, 0.25)
        except:
            experience_bonus = 0
        
        probability = max(0.15, min(0.95, base_probability - gap_penalty + experience_bonus))
        
        return round(probability, 2)
    
    def get_recommended_preparation_time(self, user):
        """
        Temps de préparation recommandé pour cet utilisateur (heures)
        """
        gaps = self.get_skill_gaps_for_user(user)
        
        if not gaps:
            return 2  # Révision minimale
        
        # 2h par compétence critique, 1h par haute priorité, 0.5h autres
        time_map = {
            'critical': 2.5,
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5,
        }
        
        total_hours = sum(time_map.get(gap['priority'], 1) for gap in gaps)
        
        # Cap à 40 heures max
        return min(int(total_hours), 40)


class LearningPathTemplate(models.Model):
    """
    Templates de parcours d'apprentissage par compétence
    Utilisé pour générer rapidement des parcours personnalisés
    """
    
    skill_name = models.CharField(
        max_length=100,
        verbose_name=_('nom de la compétence')
    )
    
    target_opportunity_type = models.CharField(
        max_length=20,
        choices=[
            ('scholarship', _('Bourse')),
            ('internship', _('Stage')),
            ('job', _('Emploi')),
            ('competition', _('Concours')),
            ('training', _('Formation')),
        ],
        verbose_name=_('type d\'opportunité cible')
    )
    
    estimated_hours = models.PositiveIntegerField(
        default=2,
        verbose_name=_('heures estimées')
    )
    
    difficulty = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_('difficulté')
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
    
    # Modules recommandés (JSONField pour flexibilité)
    recommended_modules = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('modules recommandés'),
        help_text=_('IDs ou slugs des modules MicroLearning')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'learning'
        verbose_name = _('template de parcours')
        verbose_name_plural = _('templates de parcours')
        unique_together = ['skill_name', 'target_opportunity_type']
        ordering = ['-priority', 'skill_name']
    
    def __str__(self):
        return f"{self.skill_name} ({self.get_target_opportunity_type_display()})"