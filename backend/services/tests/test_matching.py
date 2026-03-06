"""
OpportuCI - Matching Service Tests
===================================
"""
import pytest
from django.contrib.auth import get_user_model
from apps.opportunities.models import Opportunity, OpportunityCategory, ApplicationTracker
from services.matching import OpportunityMatchingService

User = get_user_model()


@pytest.mark.django_db
class TestOpportunityMatchingService:
    """Tests pour le service de matching"""

    @pytest.fixture
    def user_with_profile(self):
        """Utilisateur avec profil complet"""
        user = User.objects.create_user(
            email='dev@example.com',
            password='testpass123',
            first_name='Jean',
            last_name='Koné'
        )
        profile = user.profile
        profile.city = 'abidjan'
        profile.education_level = 'master'
        profile.field_of_study = 'Informatique'
        profile.skills = ['Python', 'Django', 'SQL', 'Machine Learning']
        profile.interests = ['tech', 'data science', 'intelligence artificielle']
        profile.languages = ['Français', 'Anglais']
        profile.save()
        return user

    @pytest.fixture
    def category(self):
        return OpportunityCategory.objects.create(
            name='Tech',
            slug='tech'
        )

    @pytest.fixture
    def matching_opportunity(self, category):
        """Opportunité qui devrait bien matcher"""
        return Opportunity.objects.create(
            title='Data Scientist Junior',
            description='Poste de Data Science avec Python',
            category=category,
            opportunity_type='job',
            organization='MTN CI',
            location='Abidjan',
            is_remote=True,
            education_level='master',
            skills_required=['Python', 'SQL', 'Machine Learning'],
            status='published'
        )

    @pytest.fixture
    def non_matching_opportunity(self, category):
        """Opportunité qui ne devrait pas matcher"""
        return Opportunity.objects.create(
            title='Médecin Généraliste',
            description='Poste médical',
            category=category,
            opportunity_type='job',
            organization='CHU Cocody',
            location='Abidjan',
            education_level='phd',
            skills_required=['Médecine', 'Chirurgie'],
            status='published'
        )

    def test_service_initialization(self):
        """Le service s'initialise correctement"""
        service = OpportunityMatchingService(use_ai=False)
        assert service.use_ai is False
        assert service._ai_service is None

    def test_heuristic_score_calculation(self, user_with_profile, matching_opportunity):
        """Le score heuristique est calculé correctement"""
        service = OpportunityMatchingService(use_ai=False)

        profile_data = user_with_profile.profile.get_matching_data()
        score, reasons = service._calculate_heuristic_score(
            profile_data,
            matching_opportunity
        )

        # Score devrait être élevé (>70) car le profil match bien
        assert score > 70
        assert len(reasons) > 0
        assert any('Python' in r or 'compétences' in r.lower() for r in reasons)

    def test_non_matching_score_lower(self, user_with_profile, matching_opportunity, non_matching_opportunity):
        """Le score pour une opportunité non-matching est plus bas que le matching"""
        service = OpportunityMatchingService(use_ai=False)

        profile_data = user_with_profile.profile.get_matching_data()

        score_matching, _ = service._calculate_heuristic_score(
            profile_data,
            matching_opportunity
        )
        score_non_matching, _ = service._calculate_heuristic_score(
            profile_data,
            non_matching_opportunity
        )

        # Le score de l'opportunité matching devrait être supérieur
        assert score_matching > score_non_matching

    def test_get_recommendations(self, user_with_profile, matching_opportunity, non_matching_opportunity):
        """Les recommandations sont triées par score"""
        service = OpportunityMatchingService(use_ai=False)

        recommendations = service.get_recommendations_for_user(
            user=user_with_profile,
            limit=10
        )

        assert len(recommendations) >= 1
        # La première recommandation devrait avoir le meilleur score
        if len(recommendations) > 1:
            assert recommendations[0]['match_score'] >= recommendations[1]['match_score']

    def test_calculate_match_for_application(self, user_with_profile, matching_opportunity):
        """Le calcul de match pour une application fonctionne"""
        service = OpportunityMatchingService(use_ai=False)

        result = service.calculate_match_for_application(
            user_with_profile,
            matching_opportunity
        )

        assert 'score' in result
        assert 'reasons' in result
        assert result['score'] is not None
        assert 0 <= result['score'] <= 100

    def test_excludes_already_applied(self, user_with_profile, matching_opportunity):
        """Les opportunités déjà postulées sont exclues"""
        # Créer une candidature
        ApplicationTracker.objects.create(
            user=user_with_profile,
            opportunity=matching_opportunity,
            status='applied'
        )

        service = OpportunityMatchingService(use_ai=False)
        recommendations = service.get_recommendations_for_user(
            user=user_with_profile,
            limit=10
        )

        # L'opportunité postulée ne devrait pas être dans les recommandations
        opp_ids = [r['opportunity'].id for r in recommendations]
        assert matching_opportunity.id not in opp_ids

    def test_user_without_profile(self):
        """Un utilisateur sans profil retourne une liste vide"""
        # Créer un user sans profil (signal désactivé pour ce test)
        from django.db.models.signals import post_save
        from apps.accounts.models.user import create_user_profile

        # Désactiver temporairement le signal
        post_save.disconnect(create_user_profile, sender=User)

        user = User.objects.create_user(
            email='noprofile@example.com',
            password='testpass123'
        )

        # Supprimer le profil s'il a été créé
        if hasattr(user, 'profile'):
            user.profile.delete()
            delattr(user, 'profile')

        service = OpportunityMatchingService(use_ai=False)
        recommendations = service.get_recommendations_for_user(user)

        # Reconnecter le signal
        post_save.connect(create_user_profile, sender=User)

        assert recommendations == []

    def test_education_level_matching(self, user_with_profile, category):
        """Le niveau d'éducation influence le score"""
        service = OpportunityMatchingService(use_ai=False)
        profile_data = user_with_profile.profile.get_matching_data()

        # Opportunité avec niveau inférieur = devrait matcher
        opp_lower = Opportunity.objects.create(
            title='Stage',
            description='Stage débutant',
            category=category,
            opportunity_type='internship',
            organization='Test',
            education_level='license',
            status='published'
        )

        score_lower, _ = service._calculate_heuristic_score(profile_data, opp_lower)

        # Opportunité avec niveau PhD = moins bon match
        opp_higher = Opportunity.objects.create(
            title='Chercheur PhD',
            description='Poste de recherche',
            category=category,
            opportunity_type='job',
            organization='Test',
            education_level='phd',
            status='published'
        )

        score_higher, _ = service._calculate_heuristic_score(profile_data, opp_higher)

        # Le niveau inférieur devrait avoir un meilleur score
        assert score_lower >= score_higher

    def test_remote_bonus(self, user_with_profile, category):
        """Les opportunités remote ont un bonus"""
        service = OpportunityMatchingService(use_ai=False)
        profile_data = user_with_profile.profile.get_matching_data()

        opp_remote = Opportunity.objects.create(
            title='Dev Remote',
            description='Travail à distance',
            category=category,
            opportunity_type='job',
            organization='Test',
            is_remote=True,
            status='published'
        )

        opp_onsite = Opportunity.objects.create(
            title='Dev Onsite',
            description='Travail sur site',
            category=category,
            opportunity_type='job',
            organization='Test',
            location='Bouaké',  # Différent de Abidjan
            is_remote=False,
            status='published'
        )

        score_remote, reasons_remote = service._calculate_heuristic_score(
            profile_data, opp_remote
        )
        score_onsite, _ = service._calculate_heuristic_score(
            profile_data, opp_onsite
        )

        assert score_remote > score_onsite
        assert any('distance' in r.lower() for r in reasons_remote)
