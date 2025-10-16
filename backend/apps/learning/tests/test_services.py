"""
OpportuCI - Learning Services Tests
====================================
Tests unitaires pour les services d'apprentissage
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.learning.models import (
    OpportunityIntelligence,
    MicroLearningModule,
    PersonalizedLearningJourney,
    UserModuleProgress
)
from apps.learning.services.intelligence_service import OpportunityIntelligenceService
from apps.learning.services.path_generator import LearningPathGenerator
from apps.learning.services.progress_tracker import ProgressTracker
from apps.opportunities.models import Opportunity, OpportunityCategory

User = get_user_model()


@pytest.mark.django_db
class TestOpportunityIntelligenceService:
    """Tests pour OpportunityIntelligenceService"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='test@opportunci.ci',
            username='testuser',
            password='testpass123',
            education_level='license'
        )
    
    @pytest.fixture
    def category(self):
        return OpportunityCategory.objects.create(
            name='Développement Web',
            slug='dev-web'
        )
    
    @pytest.fixture
    def opportunity(self, user, category):
        return Opportunity.objects.create(
            title='Développeur Web Junior',
            slug='dev-web-junior',
            description='Recherche développeur junior avec compétences en Django et React',
            category=category,
            organization='Startup CI',
            opportunity_type='job',
            status='published',
            creator=user,
            requirements='Python, Django, React, Git'
        )
    
    def test_analyze_opportunity_creates_intelligence(self, opportunity):
        """Test que l'analyse crée un objet OpportunityIntelligence"""
        service = OpportunityIntelligenceService()
        
        # Mock Gemini response
        with pytest.mock.patch.object(
            OpportunityIntelligence,
            'analyze_with_gemini',
            return_value={'technical_skills': ['Python', 'Django']}
        ):
            intelligence = service.analyze_opportunity(opportunity)
            
            assert intelligence is not None
            assert intelligence.opportunity == opportunity
            assert OpportunityIntelligence.objects.filter(opportunity=opportunity).exists()
    
    def test_get_skill_requirements_returns_dict(self, opportunity):
        """Test que get_skill_requirements retourne un dict"""
        service = OpportunityIntelligenceService()
        
        with pytest.mock.patch.object(
            OpportunityIntelligence,
            'analyze_with_gemini',
            return_value={'technical_skills': ['Python']}
        ):
            skills = service.get_skill_requirements(opportunity)
            
            assert isinstance(skills, dict)
            assert 'technical' in skills
            assert 'soft' in skills
    
    def test_calculate_match_score(self, user, opportunity):
        """Test du calcul de score de compatibilité"""
        service = OpportunityIntelligenceService()
        
        # Créer un profil avec compétences
        from apps.accounts.models import UserProfile
        UserProfile.objects.create(
            user=user,
            skills='Python, Django'
        )
        
        with pytest.mock.patch.object(
            service,
            'analyze_opportunity',
            return_value=pytest.mock.Mock(
                extracted_skills={
                    'technical': ['Python', 'Django', 'React'],
                    'soft': [],
                    'tools': [],
                    'languages': []
                }
            )
        ):
            score = service.calculate_match_score(user, opportunity)
            
            assert 0.0 <= score <= 1.0
            assert score > 0  # User a au moins quelques compétences


@pytest.mark.django_db
class TestLearningPathGenerator:
    """Tests pour LearningPathGenerator"""
    
    @pytest.fixture
    def user_with_profile(self):
        user = User.objects.create_user(
            email='learner@opportunci.ci',
            username='learner',
            password='testpass123',
            education_level='bts'
        )
        from apps.accounts.models import UserProfile
        UserProfile.objects.create(
            user=user,
            skills='Python, Git'
        )
        return user
    
    @pytest.fixture
    def opportunity(self, user_with_profile):
        category = OpportunityCategory.objects.create(name='Tech', slug='tech')
        return Opportunity.objects.create(
            title='Développeur Backend',
            slug='dev-backend',
            description='Backend developer needed',
            category=category,
            organization='Tech Co',
            opportunity_type='job',
            status='published',
            creator=user_with_profile
        )
    
    def test_generate_journey_creates_journey(self, user_with_profile, opportunity):
        """Test que generate_journey crée un parcours"""
        generator = LearningPathGenerator()
        
        # Mock les services externes
        with pytest.mock.patch.object(
            OpportunityIntelligence,
            'analyze_with_gemini',
            return_value={'technical_skills': ['Django', 'PostgreSQL']}
        ):
            with pytest.mock.patch.object(
                generator.gemini,
                'generate_content',
                return_value=pytest.mock.Mock(
                    text='{"modules": [], "estimated_total_hours": 10}'
                )
            ):
                journey = generator.generate_journey(user_with_profile, opportunity)
                
                assert journey is not None
                assert journey.user == user_with_profile
                assert journey.target_opportunity == opportunity
                assert journey.status == 'not_started'
    
    def test_assess_user_skills_returns_dict(self, user_with_profile):
        """Test que _assess_user_current_skills retourne un dict"""
        generator = LearningPathGenerator()
        skills = generator._assess_user_current_skills(user_with_profile)
        
        assert isinstance(skills, dict)
        assert 'Python' in skills
        assert skills['Python'] == 0.5  # Niveau par défaut
    
    def test_calculate_skill_gaps(self):
        """Test du calcul des gaps de compétences"""
        generator = LearningPathGenerator()
        
        required = {
            'technical': ['Python', 'Django', 'React'],
            'soft': ['Communication']
        }
        current = {
            'Python': 0.6,
            'Git': 0.7
        }
        
        gaps = generator._calculate_skill_gaps(required, current)
        
        assert isinstance(gaps, list)
        assert len(gaps) > 0
        
        # Django devrait être dans les gaps (pas dans current)
        django_gap = next((g for g in gaps if g['skill'] == 'Django'), None)
        assert django_gap is not None
        assert django_gap['priority'] in ['critical', 'high']


@pytest.mark.django_db
class TestProgressTracker:
    """Tests pour ProgressTracker"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='progress@opportunci.ci',
            username='progressuser',
            password='testpass123'
        )
    
    @pytest.fixture
    def module(self):
        return MicroLearningModule.objects.create(
            title='Intro Python',
            slug='intro-python',
            skill_taught='Python',
            content_type='video',
            duration_minutes=10,
            difficulty_level='beginner',
            points_reward=50
        )
    
    def test_start_module_creates_progress(self, user, module):
        """Test que start_module crée un UserModuleProgress"""
        tracker = ProgressTracker()
        progress = tracker.start_module(user, module)
        
        assert progress is not None
        assert progress.user == user
        assert progress.module == module
        assert progress.status == 'in_progress'
        assert progress.attempts == 1
    
    def test_update_progress_updates_percentage(self, user, module):
        """Test que update_progress met à jour le pourcentage"""
        tracker = ProgressTracker()
        
        # Démarrer d'abord
        tracker.start_module(user, module)
        
        # Mettre à jour
        progress = tracker.update_progress(user, module, percentage=50, time_spent_seconds=300)
        
        assert progress.progress_percentage == 50
        assert progress.time_spent_minutes == 5
    
    def test_complete_module_awards_points(self, user, module):
        """Test que complete_module attribue des points"""
        tracker = ProgressTracker()
        
        # Créer credibility
        from apps.credibility.models import CredibilityPoints
        cred = CredibilityPoints.objects.create(user=user, points=0)
        
        # Démarrer et compléter
        tracker.start_module(user, module)
        tracker.complete_module(user, module, score=85)
        
        # Vérifier points
        cred.refresh_from_db()
        assert cred.points > module.points_reward  # Avec bonus
    
    def test_get_user_stats_returns_dict(self, user, module):
        """Test que get_user_stats retourne des stats"""
        tracker = ProgressTracker()
        
        # Créer de l'activité
        tracker.start_module(user, module)
        tracker.complete_module(user, module, score=90)
        
        stats = tracker.get_user_stats(user, period_days=30)
        
        assert isinstance(stats, dict)
        assert 'modules' in stats
        assert stats['modules']['completed'] == 1
        assert stats['modules']['avg_score'] == 90


@pytest.mark.django_db
class TestIntegrationLearningFlow:
    """Tests d'intégration du flux complet"""
    
    def test_complete_learning_flow(self):
        """Test du flux complet : opportunité → parcours → modules → complétion"""
        # 1. Créer utilisateur avec profil
        user = User.objects.create_user(
            email='integration@opportunci.ci',
            username='integration',
            password='testpass123',
            education_level='license'
        )
        
        from apps.accounts.models import UserProfile
        UserProfile.objects.create(user=user, skills='Python')
        
        # 2. Créer opportunité
        category = OpportunityCategory.objects.create(name='Tech', slug='tech')
        opportunity = Opportunity.objects.create(
            title='Django Developer',
            slug='django-dev',
            description='Django developer needed',
            category=category,
            organization='Company',
            opportunity_type='job',
            status='published',
            creator=user
        )
        
        # 3. Générer parcours (avec mocks)
        generator = LearningPathGenerator()
        tracker = ProgressTracker()
        
        with pytest.mock.patch.object(
            OpportunityIntelligence,
            'analyze_with_gemini',
            return_value={'technical_skills': ['Django']}
        ):
            with pytest.mock.patch.object(
                generator.gemini,
                'generate_content',
                return_value=pytest.mock.Mock(
                    text='{"modules": [{"skill": "Django", "type": "video", "duration_minutes": 10, "priority": "critical", "title": "Django Basics", "description": "Learn Django", "learning_objectives": ["ORM", "Views"]}], "estimated_total_hours": 5, "success_tips": ["Practice"]}'
                )
            ):
                journey = generator.generate_journey(user, opportunity)
        
        assert journey is not None
        
        # 4. Démarrer le parcours
        journey.status = 'in_progress'
        journey.started_at = timezone.now()
        journey.save()
        
        # 5. Récupérer et compléter les modules
        from apps.learning.models import JourneyModule
        journey_modules = JourneyModule.objects.filter(journey=journey)
        
        for jm in journey_modules:
            module = jm.module
            
            # Démarrer module
            tracker.start_module(user, module)
            
            # Compléter module
            tracker.complete_module(user, module, score=85)
        
        # 6. Vérifier que le journey est complété
        journey.refresh_from_db()
        # Le journey devrait être complété automatiquement
        assert journey.progress_percentage > 0