"""
OpportuCI - Learning Models Package
====================================
Centralisation de tous les modèles d'apprentissage
"""

# Formations
from .formations import Category, Formation, Enrollment

# Cours
from .courses import Course, Lesson, UserProgress, Question, Answer, UserAnswer

# Intelligence opportunités
from .opportunity_intelligence import OpportunityIntelligence, LearningPathTemplate

# Micro-learning
from .micro_module import MicroLearningModule

# Parcours personnalisés
from .learning_journey import PersonalizedLearningJourney, JourneyModule
from .user_progress import UserModuleProgress

__all__ = [
    # Formations
    'Category',
    'Formation',
    'Enrollment',
    
    # Cours
    'Course',
    'Lesson',
    'UserProgress',
    'Question',
    'Answer',
    'UserAnswer',
    
    # Intelligence
    'OpportunityIntelligence',
    'LearningPathTemplate',
    
    # Micro-learning
    'MicroLearningModule',
    
    # Parcours
    'PersonalizedLearningJourney',
    'JourneyModule',
    'UserModulesProgress',
]
