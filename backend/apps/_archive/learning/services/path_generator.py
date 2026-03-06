"""
OpportuCI - Learning Path Generator Service
============================================
Génère des parcours d'apprentissage personnalisés avec IA
"""
import logging
import json
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.learning.models import (
    PersonalizedLearningJourney,
    MicroLearningModule,
    JourneyModule,
    OpportunityIntelligence
)
from apps.ai.services.gemini_service import GeminiAIService

logger = logging.getLogger(__name__)


class LearningPathGenerator:
    """Générateur de parcours d'apprentissage personnalisés"""
    
    def __init__(self):
        self.gemini = GeminiAIService()
        self.max_journey_hours = 40
        self.daily_learning_hours = 2
    
    @transaction.atomic
    def generate_journey(self, user, opportunity, **kwargs) -> Optional[PersonalizedLearningJourney]:
        """
        Génère un parcours complet pour un utilisateur et une opportunité
        """
        try:
            # Import ici pour éviter circular imports
            from apps.learning.services.intelligence_service import OpportunityIntelligenceService
            
            logger.info(f"Generating journey for user {user.id} -> opportunity {opportunity.id}")
            
            # 1. Analyser l'opportunité
            intelligence_service = OpportunityIntelligenceService()
            intelligence = intelligence_service.analyze_opportunity(opportunity)
            
            if not intelligence:
                logger.error(f"Failed to analyze opportunity {opportunity.id}")
                return None
            
            # 2. Créer ou récupérer le journey
            journey, created = PersonalizedLearningJourney.objects.get_or_create(
                user=user,
                target_opportunity=opportunity,
                defaults={'status': 'not_started'}
            )
            
            if not created and journey.status == 'completed':
                logger.info(f"Journey already completed for user {user.id}")
                return journey
            
            # 3. Évaluer niveau actuel utilisateur
            user_skills = self._assess_user_current_skills(user)
            journey.user_current_level = user_skills
            
            # 4. Calculer skill gaps
            skill_gaps = self._calculate_skill_gaps(
                required_skills=intelligence.extracted_skills,
                current_skills=user_skills
            )
            journey.skill_gaps = skill_gaps
            
            # 5. Générer le parcours avec IA
            path_data = self._generate_path_with_ai(user, opportunity, intelligence, skill_gaps)
            
            if not path_data:
                logger.error("Failed to generate path with AI")
                # Fallback: créer un parcours basique
                path_data = self._create_fallback_path(skill_gaps)
            
            # 6. Créer les modules
            self._create_journey_modules(journey, path_data.get('modules', []))
            
            # 7. Calculer métriques
            journey.total_estimated_hours = path_data.get('estimated_total_hours', 10)
            journey.success_probability = self._predict_success_probability(user, skill_gaps)
            journey.estimated_completion_date = self._calculate_completion_date(journey.total_estimated_hours)
            
            journey.save()
            
            # 8. Notification de bienvenue
            self._send_welcome_notification(user, journey, path_data)
            
            logger.info(f"Successfully generated journey {journey.id}")
            return journey
            
        except Exception as e:
            logger.exception(f"Error generating journey: {e}")
            return None
    
    def _assess_user_current_skills(self, user) -> Dict[str, float]:
        """Évalue les compétences actuelles de l'utilisateur"""
        skills = {}
        
        if hasattr(user, 'profile') and user.profile and user.profile.skills:
            try:
                declared_skills = user.profile.get_skills_list()
                for skill in declared_skills:
                    skills[skill.lower().strip()] = 0.5
            except:
                pass
        
        return skills
    
    def _calculate_skill_gaps(self, required_skills: Dict, current_skills: Dict) -> List[Dict]:
        """Calcule les écarts de compétences"""
        gaps = []
        
        for category, skills_list in required_skills.items():
            for skill in skills_list:
                skill_lower = skill.lower().strip()
                current_level = current_skills.get(skill_lower, 0.0)
                required_level = 0.7
                
                if current_level < required_level:
                    gap_size = required_level - current_level
                    
                    if category == 'technical':
                        priority = 'critical' if gap_size > 0.5 else 'high' if gap_size > 0.3 else 'medium'
                    else:
                        priority = 'medium' if gap_size > 0.4 else 'low'
                    
                    gaps.append({
                        'skill': skill,
                        'category': category,
                        'current': current_level,
                        'required': required_level,
                        'gap': gap_size,
                        'priority': priority
                    })
        
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        gaps.sort(key=lambda x: (priority_order[x['priority']], -x['gap']))
        
        return gaps
    
    def _generate_path_with_ai(self, user, opportunity, intelligence, skill_gaps) -> Optional[Dict]:
        """Génère le parcours optimal avec Gemini AI"""
        
        prompt = f"""
Crée un parcours d'apprentissage pour:

OPPORTUNITÉ: {opportunity.title} chez {opportunity.organization}
COMPÉTENCES MANQUANTES: {', '.join([g['skill'] for g in skill_gaps[:5]])}

Génère EXACTEMENT ce JSON (sans commentaires):
{{
    "modules": [
        {{
            "skill": "Première compétence",
            "type": "video",
            "duration_minutes": 15,
            "priority": "critical",
            "title": "Introduction à la compétence",
            "description": "Description courte",
            "learning_objectives": ["obj1", "obj2"]
        }}
    ],
    "estimated_total_hours": 10,
    "recommended_pace": "2h par jour",
    "success_tips": ["conseil 1", "conseil 2"]
}}

Limite: 8 modules maximum, durée totale max 30h.
"""
        
        try:
            response = self.gemini.generate_content(prompt)
            path_data = self._parse_ai_response(response.text)
            
            if self._validate_path_data(path_data):
                return path_data
            
        except Exception as e:
            logger.exception(f"AI generation failed: {e}")
        
        return None
    
    def _create_fallback_path(self, skill_gaps: List[Dict]) -> Dict:
        """Crée un parcours de secours si l'IA échoue"""
        modules = []
        
        for i, gap in enumerate(skill_gaps[:6]):
            modules.append({
                'skill': gap['skill'],
                'type': 'video',
                'duration_minutes': 15,
                'priority': gap['priority'],
                'title': f"Introduction à {gap['skill']}",
                'description': f"Module d'apprentissage pour {gap['skill']}",
                'learning_objectives': [f"Comprendre {gap['skill']}", f"Pratiquer {gap['skill']}"]
            })
        
        return {
            'modules': modules,
            'estimated_total_hours': len(modules) * 0.25,
            'recommended_pace': '2h par jour',
            'success_tips': ['Pratique régulière', 'Prends des notes']
        }
    
    def _create_journey_modules(self, journey: PersonalizedLearningJourney, modules_data: List[Dict]):
        """Crée et lie les modules au parcours"""
        
        for idx, module_info in enumerate(modules_data, start=1):
            module, created = MicroLearningModule.objects.get_or_create(
                skill_taught=module_info['skill'],
                title=module_info['title'],
                defaults={
                    'content_type': module_info.get('type', 'video'),
                    'duration_minutes': module_info.get('duration_minutes', 15),
                    'difficulty_level': 'intermediate',
                    'description': module_info.get('description', ''),
                    'local_examples': True,
                    'language': 'fr'
                }
            )
            
            JourneyModule.objects.get_or_create(
                journey=journey,
                module=module,
                defaults={
                    'order': idx,
                    'priority': module_info.get('priority', 'medium'),
                    'is_mandatory': module_info.get('priority', 'medium') in ['critical', 'high']
                }
            )
    
    def _predict_success_probability(self, user, skill_gaps: List[Dict]) -> float:
        """Prédit la probabilité de succès"""
        if not skill_gaps:
            return 0.95
        
        critical_gaps = len([g for g in skill_gaps if g['priority'] == 'critical'])
        avg_gap = sum(g['gap'] for g in skill_gaps) / len(skill_gaps)
        
        base_rate = 0.6
        gap_penalty = (critical_gaps * 0.15) + (avg_gap * 0.2)
        
        probability = base_rate - gap_penalty
        return round(min(0.95, max(0.2, probability)), 2)
    
    def _calculate_completion_date(self, total_hours: int):
        """Estime la date de complétion"""
        days_needed = int((total_hours / self.daily_learning_hours) * 1.2)
        return timezone.now().date() + timedelta(days=days_needed)
    
    def _send_welcome_notification(self, user, journey, path_data):
        """Notification de bienvenue"""
        try:
            from apps.notifications.services import create_notification
            
            first_module = path_data.get('modules', [{}])[0]
            
            message = f"""
🎯 Ton parcours est prêt !

Objectif : {journey.target_opportunity.title}
Durée : {journey.total_estimated_hours}h
Succès : {int(journey.success_probability * 100)}%

Premier module : {first_module.get('title', 'À déterminer')}

C'est parti ! 🚀
"""
            
            create_notification(
                user=user,
                title="Parcours prêt !",
                message=message,
                notification_type='system'
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _parse_ai_response(self, text: str) -> Dict:
        """Parse la réponse JSON de Gemini"""
        try:
            text = text.strip()
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {}
    
    def _validate_path_data(self, path_data: Dict) -> bool:
        """Valide les données du parcours"""
        if not isinstance(path_data, dict):
            return False
        
        if 'modules' not in path_data or not isinstance(path_data['modules'], list):
            return False
        
        if len(path_data['modules']) == 0:
            return False
        
        if path_data.get('estimated_total_hours', 0) > self.max_journey_hours:
            return False
        
        return True