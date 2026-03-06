"""
OpportuCI - Opportunity Intelligence Service
=============================================
Service pour analyser automatiquement les opportunités avec Gemini AI
"""
import logging
from typing import Dict, List, Optional
from django.core.cache import cache
from apps.learning.models import OpportunityIntelligence
from apps.opportunities.models import Opportunity
from apps.ai.services.gemini_service import GeminiAIService

logger = logging.getLogger(__name__)


class OpportunityIntelligenceService:
    """Service d'analyse intelligente des opportunités"""
    
    def __init__(self):
        self.gemini = GeminiAIService()
        self.cache_timeout = 86400  # 24h
    
    def analyze_opportunity(self, opportunity: Opportunity, force_refresh: bool = False) -> Optional[OpportunityIntelligence]:
        """
        Analyse une opportunité et extrait les compétences requises
        
        Args:
            opportunity: L'opportunité à analyser
            force_refresh: Force une nouvelle analyse même si cache existe
            
        Returns:
            OpportunityIntelligence object ou None si erreur
        """
        # Vérifier cache
        cache_key = f"opp_intelligence_{opportunity.id}"
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for opportunity {opportunity.id}")
                return cached
        
        try:
            # Récupérer ou créer l'objet
            intelligence, created = OpportunityIntelligence.objects.get_or_create(
                opportunity=opportunity
            )
            
            # Analyser avec Gemini
            logger.info(f"Analyzing opportunity {opportunity.id} with Gemini AI")
            analysis_result = intelligence.analyze_with_gemini()
            
            if analysis_result:
                # Mettre en cache
                cache.set(cache_key, intelligence, self.cache_timeout)
                logger.info(f"Successfully analyzed opportunity {opportunity.id}")
                return intelligence
            else:
                logger.error(f"Failed to analyze opportunity {opportunity.id}")
                return None
                
        except Exception as e:
            logger.exception(f"Error analyzing opportunity {opportunity.id}: {e}")
            return None
    
    def get_skill_requirements(self, opportunity: Opportunity) -> Dict[str, List[str]]:
        """
        Récupère les compétences requises pour une opportunité
        
        Returns:
            Dict avec 'technical', 'soft', 'tools', 'languages'
        """
        intelligence = self.analyze_opportunity(opportunity)
        
        if intelligence:
            return intelligence.extracted_skills
        
        # Fallback si analyse échoue
        return {
            'technical': [],
            'soft': [],
            'tools': [],
            'languages': ['Français']
        }
    
    def calculate_match_score(self, user, opportunity: Opportunity) -> float:
        """
        Calcule le score de compatibilité utilisateur <-> opportunité
        
        Returns:
            Score entre 0.0 et 1.0
        """
        intelligence = self.analyze_opportunity(opportunity)
        
        if not intelligence:
            return 0.5  # Score neutre par défaut
        
        # Récupérer compétences utilisateur
        user_skills = self._get_user_skills(user)
        
        # Compétences requises
        required_skills = []
        for category, skills in intelligence.extracted_skills.items():
            required_skills.extend(skills)
        
        if not required_skills:
            return 0.5
        
        # Calculer intersection
        matching_skills = set(user_skills) & set(required_skills)
        match_ratio = len(matching_skills) / len(required_skills)
        
        # Bonus pour niveau d'éducation
        education_bonus = self._calculate_education_match(user, intelligence)
        
        # Score final (70% skills, 30% education)
        final_score = (match_ratio * 0.7) + (education_bonus * 0.3)
        
        return min(1.0, max(0.0, final_score))
    
    def get_recommended_preparation_time(self, user, opportunity: Opportunity) -> int:
        """
        Estime le temps de préparation nécessaire en heures
        
        Returns:
            Nombre d'heures estimées
        """
        intelligence = self.analyze_opportunity(opportunity)
        
        if not intelligence:
            return 10  # Défaut 10h
        
        base_time = intelligence.estimated_preparation_hours
        
        # Ajuster selon niveau utilisateur
        match_score = self.calculate_match_score(user, opportunity)
        
        if match_score > 0.8:
            # Utilisateur déjà bien préparé
            return max(2, int(base_time * 0.3))
        elif match_score > 0.5:
            # Niveau moyen
            return base_time
        else:
            # Beaucoup de préparation nécessaire
            return int(base_time * 1.5)
    
    def _get_user_skills(self, user) -> List[str]:
        """Extrait la liste des compétences de l'utilisateur"""
        if hasattr(user, 'profile') and user.profile.skills:
            return user.profile.get_skills_list()
        return []
    
    def _calculate_education_match(self, user, intelligence: OpportunityIntelligence) -> float:
        """Calcule la compatibilité du niveau d'éducation"""
        if not intelligence.opportunity.education_level:
            return 0.5
        
        # Mapping des niveaux
        education_hierarchy = {
            'secondary': 1,
            'baccalaureate': 2,
            'bts': 3,
            'license': 4,
            'master': 5,
            'phd': 6
        }
        
        user_level = education_hierarchy.get(user.education_level, 0)
        required_level_str = intelligence.opportunity.education_level.lower()
        
        # Chercher le niveau dans la description
        for level, rank in education_hierarchy.items():
            if level in required_level_str:
                required_level = rank
                break
        else:
            required_level = 3  # Défaut BTS
        
        # Score selon écart
        if user_level >= required_level:
            return 1.0
        elif user_level == required_level - 1:
            return 0.7
        else:
            return 0.4
    
    def bulk_analyze_opportunities(self, opportunity_ids: List[int], batch_size: int = 10):
        """
        Analyse plusieurs opportunités en batch (async avec Celery)
        
        Args:
            opportunity_ids: Liste des IDs d'opportunités
            batch_size: Taille des batches
        """
        from apps.learning.tasks import analyze_opportunity_task
        
        for i in range(0, len(opportunity_ids), batch_size):
            batch = opportunity_ids[i:i+batch_size]
            
            for opp_id in batch:
                # Lancer tâche Celery asynchrone
                analyze_opportunity_task.delay(opp_id)
        
        logger.info(f"Launched {len(opportunity_ids)} analysis tasks")