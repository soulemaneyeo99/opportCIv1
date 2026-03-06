"""
OpportuCI - Opportunity Matching Service
=========================================
Orchestre le matching IA entre profils et opportunités.
"""
import logging
from typing import List, Dict, Optional
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class OpportunityMatchingService:
    """
    Service principal de matching IA
    
    Combine algorithme heuristique + IA pour recommander
    les meilleures opportunités à chaque utilisateur.
    """
    
    def __init__(self, use_ai: bool = True):
        """
        Args:
            use_ai: Active l'enrichissement IA (désactiver pour les tests)
        """
        self.use_ai = use_ai
        self._ai_service = None
    
    @property
    def ai_service(self):
        """Lazy loading du service IA"""
        if self._ai_service is None and self.use_ai:
            try:
                from apps.ai.services.gemini_service import GeminiAIService
                self._ai_service = GeminiAIService()
            except Exception as e:
                logger.warning(f"IA indisponible: {e}")
                self._ai_service = None
        return self._ai_service
    
    def get_recommendations_for_user(
        self,
        user,
        limit: int = 10,
        opportunity_type: str = None
    ) -> List[Dict]:
        """
        Génère des recommandations personnalisées pour un utilisateur.
        
        Args:
            user: Instance User avec profile
            limit: Nombre max de recommandations
            opportunity_type: Filtrer par type (scholarship, internship, job...)
            
        Returns:
            Liste de dicts avec opportunity, score, reasons
        """
        from apps.opportunities.models import Opportunity, ApplicationTracker
        
        # Récupérer le profil
        if not hasattr(user, 'profile'):
            logger.warning(f"User {user.id} sans profil")
            return []
        
        profile = user.profile
        profile_data = profile.get_matching_data()
        
        # Opportunités candidates (publiées, non expirées)
        candidates = Opportunity.objects.filter(
            status='published'
        ).exclude(
            deadline__lt=timezone.now()
        ).select_related('category')
        
        if opportunity_type:
            candidates = candidates.filter(opportunity_type=opportunity_type)
        
        # Exclure celles déjà postulées
        applied_ids = ApplicationTracker.objects.filter(
            user=user,
            status__in=['applied', 'interviewing', 'offer', 'accepted']
        ).values_list('opportunity_id', flat=True)
        
        candidates = candidates.exclude(id__in=applied_ids)
        
        # Scoring heuristique rapide
        scored_opportunities = []
        for opp in candidates[:100]:  # Limite pour perfs
            score, reasons = self._calculate_heuristic_score(profile_data, opp)
            if score > 20:  # Seuil minimum
                scored_opportunities.append({
                    'opportunity': opp,
                    'score': score,
                    'reasons': reasons,
                    'opp_data': opp.get_matching_data()
                })
        
        # Trier par score décroissant
        scored_opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Top candidats pour enrichissement IA
        top_candidates = scored_opportunities[:limit * 2]
        
        # Enrichissement IA si disponible
        if self.ai_service and top_candidates:
            top_candidates = self._enrich_with_ai(
                profile_data,
                top_candidates,
                limit
            )
        
        # Retourner les meilleurs
        results = []
        for item in top_candidates[:limit]:
            results.append({
                'opportunity': item['opportunity'],
                'match_score': item['score'],
                'match_reasons': item['reasons'],
                'ai_enhanced': item.get('ai_enhanced', False)
            })
        
        return results
    
    def calculate_match_for_application(
        self,
        user,
        opportunity
    ) -> Dict:
        """
        Calcule le score de matching pour une candidature spécifique.
        Utilisé quand l'utilisateur découvre/sauvegarde une opportunité.
        
        Returns:
            Dict avec score (0-100) et reasons (liste)
        """
        if not hasattr(user, 'profile'):
            return {'score': None, 'reasons': []}
        
        profile_data = user.profile.get_matching_data()
        score, reasons = self._calculate_heuristic_score(profile_data, opportunity)
        
        # Enrichissement IA pour les scores détaillés
        if self.ai_service:
            try:
                ai_result = self._get_ai_match_details(
                    profile_data,
                    opportunity.get_matching_data()
                )
                if ai_result:
                    # Pondérer heuristique (40%) + IA (60%)
                    score = int(score * 0.4 + ai_result.get('score', score) * 0.6)
                    reasons = ai_result.get('reasons', reasons)
            except Exception as e:
                logger.error(f"Erreur AI match: {e}")
        
        return {
            'score': min(100, max(0, score)),
            'reasons': reasons[:5]
        }
    
    def _calculate_heuristic_score(
        self,
        profile: Dict,
        opportunity
    ) -> tuple:
        """
        Calcul rapide de score sans IA (heuristique).
        
        Returns:
            (score: int, reasons: list)
        """
        score = 50  # Score de base
        reasons = []
        
        opp_data = opportunity.get_matching_data()
        
        # 1. Match compétences (max +25)
        user_skills = set(s.lower() for s in (profile.get('skills') or []))
        required_skills = set(s.lower() for s in (opp_data.get('skills_required') or []))
        
        if required_skills:
            matching_skills = user_skills & required_skills
            skill_match_ratio = len(matching_skills) / len(required_skills)
            skill_bonus = int(skill_match_ratio * 25)
            score += skill_bonus
            
            if matching_skills:
                reasons.append(
                    f"Compétences correspondantes: {', '.join(list(matching_skills)[:3])}"
                )
        else:
            score += 10  # Pas d'exigences = accessible
        
        # 2. Match niveau éducation (max +15)
        education_levels = {
            'secondary': 1, 'bac': 2, 'bts': 3,
            'license': 4, 'master': 5, 'phd': 6, 'any': 0
        }
        user_level = education_levels.get(profile.get('education_level'), 0)
        required_level = education_levels.get(opp_data.get('education_level'), 0)
        
        if required_level == 0 or user_level >= required_level:
            score += 15
            reasons.append("Niveau d'études compatible")
        elif user_level == required_level - 1:
            score += 8
            reasons.append("Niveau d'études proche du requis")
        
        # 3. Match intérêts (max +15)
        user_interests = set(i.lower() for i in (profile.get('interests') or []))
        opp_category = (opp_data.get('category') or '').lower()
        opp_type = (opp_data.get('type') or '').lower()
        
        interest_keywords = {
            'tech': ['informatique', 'développement', 'digital', 'it'],
            'finance': ['banque', 'comptabilité', 'économie'],
            'santé': ['médecine', 'pharmaceutique', 'hôpital'],
            'education': ['enseignement', 'formation', 'pédagogie']
        }
        
        for interest in user_interests:
            if interest in opp_category or interest in opp_type:
                score += 10
                reasons.append(f"Correspond à votre intérêt: {interest}")
                break
        
        # 4. Match localisation (max +10)
        user_city = (profile.get('location') or '').lower()
        opp_location = (opp_data.get('location') or '').lower()
        is_remote = opp_data.get('is_remote', False)
        
        if is_remote:
            score += 10
            reasons.append("Travail à distance possible")
        elif user_city and user_city in opp_location:
            score += 10
            reasons.append(f"Localisé à {user_city.title()}")
        
        # 5. Bonus deadline proche (+5)
        if hasattr(opportunity, 'days_until_deadline'):
            days = opportunity.days_until_deadline
            if days and 3 <= days <= 14:
                score += 5
                reasons.append(f"Date limite dans {days} jours")
        
        return score, reasons
    
    def _enrich_with_ai(
        self,
        profile: Dict,
        candidates: List[Dict],
        limit: int
    ) -> List[Dict]:
        """
        Enrichit les scores avec l'IA Gemini.
        """
        if not self.ai_service:
            return candidates
        
        try:
            # Préparer les données pour l'IA
            opportunities_data = [c['opp_data'] for c in candidates]
            
            ai_recommendations = self.ai_service.get_opportunity_recommendations(
                user_profile=profile,
                opportunities=opportunities_data,
                limit=limit
            )
            
            # Mapper les résultats IA aux candidats
            ai_map = {
                str(rec.get('opportunity_id')): rec
                for rec in ai_recommendations
            }
            
            for candidate in candidates:
                opp_id = str(candidate['opportunity'].id)
                if opp_id in ai_map:
                    ai_rec = ai_map[opp_id]
                    # Combiner scores
                    ai_score = int(ai_rec.get('match_score', 0) * 100)
                    candidate['score'] = int(
                        candidate['score'] * 0.3 + ai_score * 0.7
                    )
                    candidate['reasons'] = [ai_rec.get('match_reason')] + \
                        ai_rec.get('key_advantages', [])
                    candidate['ai_enhanced'] = True
            
            # Re-trier
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Erreur enrichissement IA: {e}")
        
        return candidates
    
    def _get_ai_match_details(
        self,
        profile: Dict,
        opportunity: Dict
    ) -> Optional[Dict]:
        """
        Obtient les détails de match IA pour une opportunité unique.
        """
        if not self.ai_service:
            return None
        
        try:
            results = self.ai_service.get_opportunity_recommendations(
                user_profile=profile,
                opportunities=[opportunity],
                limit=1
            )
            
            if results:
                rec = results[0]
                return {
                    'score': int(rec.get('match_score', 0) * 100),
                    'reasons': [rec.get('match_reason')] + \
                        rec.get('key_advantages', [])
                }
        except Exception as e:
            logger.error(f"Erreur AI match details: {e}")
        
        return None
    
    def update_application_match_score(self, application) -> None:
        """
        Met à jour le score de matching d'une ApplicationTracker.
        À appeler quand l'utilisateur découvre/sauvegarde une opportunité.
        """
        try:
            match_data = self.calculate_match_for_application(
                application.user,
                application.opportunity
            )
            
            application.ai_match_score = match_data['score']
            application.ai_match_reasons = match_data['reasons']
            application.save(update_fields=['ai_match_score', 'ai_match_reasons'])
            
        except Exception as e:
            logger.error(f"Erreur update match score: {e}")
