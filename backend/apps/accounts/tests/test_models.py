"""
OpportuCI - Accounts Models Tests
==================================
"""
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests pour le modèle User"""

    def test_create_user(self):
        """Créer un utilisateur avec email"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_without_email_fails(self):
        """Créer un utilisateur sans email doit échouer"""
        with pytest.raises(ValueError) as exc_info:
            User.objects.create_user(email='', password='testpass123')
        # Le message est en français: "L'adresse e-mail est obligatoire"
        assert 'e-mail' in str(exc_info.value).lower()

    def test_create_superuser(self):
        """Créer un superuser"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.is_staff
        assert admin.is_superuser

    def test_email_normalized(self):
        """L'email doit être normalisé (domaine en minuscules)"""
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            password='testpass123'
        )
        # Normalize_email garde la partie locale, met le domaine en minuscules
        assert user.email == 'Test@example.com'

    def test_get_full_name(self):
        """Tester get_full_name()"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Jean',
            last_name='Dupont'
        )
        assert user.get_full_name() == 'Jean Dupont'

    def test_get_full_name_without_names(self):
        """get_full_name() retourne la partie locale de l'email si pas de nom"""
        user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        # Retourne email.split('@')[0] si pas de prénom/nom
        assert user.get_full_name() == 'testuser'

    def test_user_str(self):
        """Test __str__() du User"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert str(user) == 'test@example.com'

    def test_user_type_default(self):
        """Le type utilisateur par défaut est 'student'"""
        user = User.objects.create_user(
            email='student@example.com',
            password='testpass123'
        )
        assert user.user_type == 'student'

    def test_profile_auto_created(self):
        """Un profil est automatiquement créé avec l'utilisateur"""
        user = User.objects.create_user(
            email='auto@example.com',
            password='testpass123'
        )
        assert hasattr(user, 'profile')
        assert user.profile is not None


@pytest.mark.django_db
class TestProfileModel:
    """Tests pour le modèle Profile"""

    def test_profile_created_with_user(self):
        """Le profil est créé automatiquement avec l'utilisateur"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, Profile)

    def test_update_profile(self):
        """Mettre à jour un profil existant"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.profile.city = 'yamoussoukro'
        user.profile.education_level = 'license'
        user.profile.save()

        # Recharger depuis la DB
        user.refresh_from_db()
        assert user.profile.city == 'yamoussoukro'
        assert user.profile.education_level == 'license'

    def test_profile_skills_json(self):
        """Tester le champ skills JSONField"""
        user = User.objects.create_user(
            email='dev@example.com',
            password='testpass123'
        )
        user.profile.skills = ['Python', 'Django', 'PostgreSQL']
        user.profile.save()

        user.refresh_from_db()
        assert 'Python' in user.profile.skills
        assert len(user.profile.skills) == 3

    def test_profile_interests_json(self):
        """Tester le champ interests JSONField"""
        user = User.objects.create_user(
            email='student@example.com',
            password='testpass123'
        )
        user.profile.interests = ['data science', 'machine learning']
        user.profile.save()

        user.refresh_from_db()
        assert 'data science' in user.profile.interests

    def test_profile_languages_json(self):
        """Tester le champ languages JSONField"""
        user = User.objects.create_user(
            email='polyglot@example.com',
            password='testpass123'
        )
        user.profile.languages = ['Français', 'Anglais', 'Espagnol']
        user.profile.save()

        user.refresh_from_db()
        assert len(user.profile.languages) == 3

    def test_get_matching_data(self):
        """Tester la méthode get_matching_data()"""
        user = User.objects.create_user(
            email='match@example.com',
            password='testpass123',
            first_name='Marie',
            last_name='Koné'
        )
        profile = user.profile
        profile.city = 'abidjan'
        profile.education_level = 'master'
        profile.field_of_study = 'Informatique'
        profile.skills = ['Python', 'Data Science']
        profile.interests = ['IA', 'Big Data']
        profile.languages = ['Français', 'Anglais']
        profile.save()

        matching_data = profile.get_matching_data()

        assert matching_data['name'] == 'Marie Koné'
        assert matching_data['education_level'] == 'master'
        assert 'Python' in matching_data['skills']
        assert 'IA' in matching_data['interests']
        assert 'Français' in matching_data['languages']

    def test_profile_str(self):
        """Test __str__() du Profile"""
        user = User.objects.create_user(
            email='str@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert 'Test User' in str(user.profile)

    def test_profile_default_city(self):
        """La ville par défaut est Abidjan"""
        user = User.objects.create_user(
            email='default@example.com',
            password='testpass123'
        )
        assert user.profile.city == 'abidjan'
