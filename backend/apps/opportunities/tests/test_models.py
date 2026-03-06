"""
OpportuCI - Opportunities Models Tests
=======================================
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from apps.opportunities.models import (
    Opportunity,
    OpportunityCategory,
    OpportunitySource,
    ApplicationTracker
)

User = get_user_model()


@pytest.mark.django_db
class TestOpportunityCategoryModel:
    """Tests pour OpportunityCategory"""

    def test_create_category(self):
        """Créer une catégorie"""
        category = OpportunityCategory.objects.create(
            name='Bourses',
            description='Bourses d\'études'
        )
        assert category.name == 'Bourses'
        assert category.slug == 'bourses'
        assert category.is_active

    def test_category_slug_auto_generated(self):
        """Le slug est généré automatiquement"""
        category = OpportunityCategory.objects.create(
            name='Formation Professionnelle'
        )
        assert category.slug == 'formation-professionnelle'

    def test_category_str(self):
        """Test __str__()"""
        category = OpportunityCategory.objects.create(name='Stages')
        assert str(category) == 'Stages'


@pytest.mark.django_db
class TestOpportunitySourceModel:
    """Tests pour OpportunitySource"""

    def test_create_source(self):
        """Créer une source"""
        source = OpportunitySource.objects.create(
            name='Campus France',
            source_type='website',
            url='https://campusfrance.org'
        )
        assert source.name == 'Campus France'
        assert source.source_type == 'website'
        assert source.is_active

    def test_source_str(self):
        """Test __str__()"""
        source = OpportunitySource.objects.create(
            name='Partenaire Local',
            source_type='partner'
        )
        assert 'Partenaire Local' in str(source)
        assert 'Partenaire' in str(source)


@pytest.mark.django_db
class TestOpportunityModel:
    """Tests pour le modèle Opportunity"""

    @pytest.fixture
    def category(self):
        return OpportunityCategory.objects.create(name='Bourses')

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='creator@example.com',
            password='testpass123'
        )

    def test_create_opportunity(self, category):
        """Créer une opportunité"""
        opp = Opportunity.objects.create(
            title='Bourse Eiffel 2025',
            description='Programme de bourses du gouvernement français',
            category=category,
            opportunity_type='scholarship',
            organization='Campus France',
            status='published'
        )
        assert opp.title == 'Bourse Eiffel 2025'
        assert opp.opportunity_type == 'scholarship'
        assert str(opp.id)  # UUID généré

    def test_slug_auto_generated(self, category):
        """Le slug est généré automatiquement"""
        opp = Opportunity.objects.create(
            title='Stage Data Science Orange CI',
            description='Stage de 6 mois',
            category=category,
            opportunity_type='internship',
            organization='Orange CI'
        )
        assert 'stage-data-science-orange-ci' in opp.slug

    def test_slug_unique(self, category):
        """Les slugs doivent être uniques"""
        opp1 = Opportunity.objects.create(
            title='Stage Développeur',
            description='Desc 1',
            category=category,
            opportunity_type='internship',
            organization='Org 1'
        )
        opp2 = Opportunity.objects.create(
            title='Stage Développeur',
            description='Desc 2',
            category=category,
            opportunity_type='internship',
            organization='Org 2'
        )
        assert opp1.slug != opp2.slug
        assert opp2.slug.startswith('stage-developpeur')

    def test_is_expired_property(self, category):
        """Tester la propriété is_expired"""
        # Opportunité expirée
        expired = Opportunity.objects.create(
            title='Opportunité Passée',
            description='Test',
            category=category,
            opportunity_type='job',
            organization='Test',
            deadline=timezone.now() - timedelta(days=1)
        )
        assert expired.is_expired

        # Opportunité active
        active = Opportunity.objects.create(
            title='Opportunité Future',
            description='Test',
            category=category,
            opportunity_type='job',
            organization='Test',
            deadline=timezone.now() + timedelta(days=30)
        )
        assert not active.is_expired

    def test_days_until_deadline(self, category):
        """Tester days_until_deadline"""
        opp = Opportunity.objects.create(
            title='Test Deadline',
            description='Test',
            category=category,
            opportunity_type='scholarship',
            organization='Test',
            deadline=timezone.now() + timedelta(days=10)
        )
        assert 9 <= opp.days_until_deadline <= 10

    def test_skills_required_json(self, category):
        """Tester le champ skills_required JSONField"""
        opp = Opportunity.objects.create(
            title='Poste Tech',
            description='Développeur',
            category=category,
            opportunity_type='job',
            organization='Tech Corp',
            skills_required=['Python', 'Django', 'PostgreSQL']
        )
        assert 'Python' in opp.skills_required
        assert len(opp.skills_required) == 3

    def test_get_matching_data(self, category):
        """Tester la méthode get_matching_data()"""
        opp = Opportunity.objects.create(
            title='Stage Data Analyst',
            description='Stage de fin d\'études en data analyse',
            category=category,
            opportunity_type='internship',
            organization='MTN CI',
            location='Abidjan',
            is_remote=True,
            education_level='master',
            skills_required=['Python', 'SQL', 'Tableau'],
            experience_years=0
        )

        data = opp.get_matching_data()

        assert data['title'] == 'Stage Data Analyst'
        assert data['organization'] == 'MTN CI'
        assert data['type'] == 'internship'
        assert data['is_remote'] is True
        assert 'Python' in data['skills_required']

    def test_opportunity_str(self, category):
        """Test __str__()"""
        opp = Opportunity.objects.create(
            title='Test Opportunité',
            description='Test',
            category=category,
            opportunity_type='training',
            organization='Test'
        )
        assert str(opp) == 'Test Opportunité'


@pytest.mark.django_db
class TestApplicationTrackerModel:
    """Tests pour ApplicationTracker"""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='applicant@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def opportunity(self):
        category = OpportunityCategory.objects.create(name='Jobs')
        return Opportunity.objects.create(
            title='Emploi Test',
            description='Test',
            category=category,
            opportunity_type='job',
            organization='Test Corp'
        )

    def test_create_application(self, user, opportunity):
        """Créer un suivi de candidature"""
        tracker = ApplicationTracker.objects.create(
            user=user,
            opportunity=opportunity
        )
        assert tracker.status == 'discovered'
        assert tracker.user == user
        assert tracker.opportunity == opportunity

    def test_application_status_flow(self, user, opportunity):
        """Tester le flux de statut"""
        tracker = ApplicationTracker.objects.create(
            user=user,
            opportunity=opportunity
        )

        # Sauvegarder
        tracker.update_status('saved', 'Intéressant')
        assert tracker.status == 'saved'
        assert tracker.saved_at is not None

        # Postuler
        tracker.update_status('applied', 'CV envoyé')
        assert tracker.status == 'applied'
        assert tracker.applied_at is not None

    def test_ai_match_score(self, user, opportunity):
        """Tester le score de matching IA"""
        tracker = ApplicationTracker.objects.create(
            user=user,
            opportunity=opportunity,
            ai_match_score=85.5,
            ai_match_reasons=['Compétences correspondantes', 'Niveau d\'études compatible']
        )
        assert tracker.ai_match_score == 85.5
        assert len(tracker.ai_match_reasons) == 2

    def test_unique_user_opportunity(self, user, opportunity):
        """Un utilisateur ne peut avoir qu'un tracker par opportunité"""
        ApplicationTracker.objects.create(
            user=user,
            opportunity=opportunity
        )

        with pytest.raises(Exception):  # IntegrityError
            ApplicationTracker.objects.create(
                user=user,
                opportunity=opportunity
            )

    def test_application_str(self, user, opportunity):
        """Test __str__()"""
        tracker = ApplicationTracker.objects.create(
            user=user,
            opportunity=opportunity
        )
        assert user.email in str(tracker)
        assert opportunity.title in str(tracker)
