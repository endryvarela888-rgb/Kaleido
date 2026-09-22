import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.tiers.models import Tier


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='fan@example.com',
        password='supersecret123',
        display_name='Test Fan',
        is_active=True,
    )


@pytest.fixture
def creator(db):
    user = User.objects.create_user(
        email='creator@example.com',
        password='supersecret123',
        display_name='Test Creator',
        is_active=True,
        is_creator=True,
    )
    return user


@pytest.fixture
def tier(db, creator):
    return Tier.objects.create(
        creator=creator,
        name='Supporter',
        price=5.00,
        level=1,
    )


def _authenticated_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def auth_client(user):
    """API client already logged in as a regular (non-creator) user."""
    return _authenticated_client(user)


@pytest.fixture
def creator_client(creator):
    """API client already logged in as the creator."""
    return _authenticated_client(creator)