# ===================================================================
# apps/learning/utils.py - Fonctions Utilitaires
# ===================================================================

"""
OpportuCI - Learning Utilities
===============================
Fonctions helper pour le module learning
"""
from typing import List, Dict
import re


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extrait des compétences potentielles d'un texte
    Utilise des patterns simples (à améliorer avec NLP)
    
    Args:
        text: Texte à analyser (description, requirements, etc.)
        
    Returns:
        Liste de compétences détectées
    """
    # Liste de compétences communes (à étendre)
    common_skills = [
        # Tech
        'python', 'javascript', 'java', 'c++', 'react', 'django', 'nodejs',
        'sql', 'mongodb', 'postgresql', 'git', 'docker', 'kubernetes',
        'html', 'css', 'typescript', 'vue', 'angular', 'php', 'laravel',
        
        # Data
        'excel', 'powerpoint', 'word', 'data analysis', 'tableau', 'power bi',
        'machine learning', 'ai', 'deep learning', 'statistics',
        
        # Soft skills
        'communication', 'leadership', 'teamwork', 'problem solving',
        'critical thinking', 'creativity', 'adaptability',
        
        # Business
        'marketing', 'sales', 'project management', 'agile', 'scrum',
        'customer service', 'crm', 'seo', 'social media',
        
        # Design
        'photoshop', 'illustrator', 'figma', 'canva', 'ui/ux', 'design thinking'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))  # Dédupliquer


def format_duration_text(minutes: int) -> str:
    """
    Convertit une durée en minutes en texte lisible
    
    Args:
        minutes: Durée en minutes
        
    Returns:
        Texte formaté (ex: "2h 30min")
    """
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    
    return f"{hours}h {remaining_minutes}min"


def calculate_estimated_completion_date(total_hours: int, daily_hours: int = 2) -> str:
    """
    Calcule une date estimée de complétion
    
    Args:
        total_hours: Total d'heures nécessaires
        daily_hours: Heures d'apprentissage par jour
        
    Returns:
        Texte formaté (ex: "Dans 2 semaines")
    """
    from datetime import timedelta
    from django.utils import timezone
    
    days_needed = int((total_hours / daily_hours) * 1.2)  # +20% buffer
    
    if days_needed <= 7:
        return f"Dans {days_needed} jours"
    elif days_needed <= 30:
        weeks = days_needed // 7
        return f"Dans {weeks} semaine{'s' if weeks > 1 else ''}"
    else:
        months = days_needed // 30
        return f"Dans {months} mois"


def get_difficulty_color(difficulty: str) -> str:
    """
    Retourne une couleur Tailwind selon la difficulté
    
    Args:
        difficulty: 'beginner', 'intermediate', 'advanced'
        
    Returns:
        Classe CSS Tailwind
    """
    colors = {
        'beginner': 'text-green-600 bg-green-50',
        'intermediate': 'text-yellow-600 bg-yellow-50',
        'advanced': 'text-red-600 bg-red-50'
    }
    return colors.get(difficulty, 'text-gray-600 bg-gray-50')


def get_priority_badge_class(priority: str) -> str:
    """
    Retourne une classe CSS selon la priorité
    
    Args:
        priority: 'critical', 'high', 'medium', 'low'
        
    Returns:
        Classes CSS Tailwind
    """
    classes = {
        'critical': 'bg-red-100 text-red-800 border-red-300',
        'high': 'bg-orange-100 text-orange-800 border-orange-300',
        'medium': 'bg-yellow-100 text-yellow-800 border-yellow-300',
        'low': 'bg-green-100 text-green-800 border-green-300'
    }
    return classes.get(priority, 'bg-gray-100 text-gray-800')


def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """
    Nettoie et sécurise les entrées utilisateur
    
    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale
        
    Returns:
        Texte nettoyé
    """
    # Supprimer HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Supprimer caractères dangereux
    clean = re.sub(r'[<>&"\']', '', clean)
    
    # Tronquer
    return clean[:max_length].strip()