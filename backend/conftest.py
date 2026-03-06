"""
OpportuCI - Pytest Configuration
=================================
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user_password():
    """Mot de passe standard pour les tests"""
    return 'testpass123'


@pytest.fixture
def create_user(db, user_password):
    """Factory pour créer des utilisateurs"""
    def _create_user(
        email='test@example.com',
        password=None,
        first_name='Test',
        last_name='User',
        **kwargs
    ):
        return User.objects.create_user(
            email=email,
            password=password or user_password,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
    return _create_user


@pytest.fixture
def user(create_user):
    """Utilisateur de test standard"""
    return create_user()


@pytest.fixture
def admin_user(db, user_password):
    """Utilisateur admin de test"""
    return User.objects.create_superuser(
        email='admin@example.com',
        password=user_password
    )


@pytest.fixture
def api_client():
    """Client API REST Framework"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, user_password):
    """Client API authentifié"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client
