import pytest
from django.urls import reverse

from apps.users.models import User
from apps.users.tokens import account_activation_token


from unittest.mock import patch


@pytest.mark.django_db
class TestSignup:
    @patch('apps.users.api_views._send_activation_email')
    def test_signup_creates_inactive_user(self, mock_send_email, api_client):
        url = reverse('users_api:signup')
        payload = {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password': 'supersecret123',
        }

        response = api_client.post(url, payload)

        assert response.status_code == 201
        user = User.objects.get(email='newuser@example.com')
        assert user.is_active is False
        assert user.check_password('supersecret123')
        mock_send_email.assert_called_once()


@pytest.mark.django_db
class TestActivation:
    def test_activation_activates_user_and_returns_tokens(self, api_client):
        user = User.objects.create_user(
            email='inactive@example.com',
            password='supersecret123',
            display_name='Inactive User',
            is_active=False,
        )
        token = account_activation_token.make_token(user)
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        url = reverse('users_api:activate')
        response = api_client.post(url, {'uid': uid, 'token': token})

        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        user.refresh_from_db()
        assert user.is_active is True

    def test_activation_rejects_invalid_token(self, api_client, user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        url = reverse('users_api:activate')
        response = api_client.post(url, {'uid': uid, 'token': 'garbage-token'})

        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_succeeds_with_correct_credentials(self, api_client, user):
        url = reverse('users_api:token_obtain')
        response = api_client.post(url, {'email': user.email, 'password': 'supersecret123'})

        assert response.status_code == 200
        assert 'access' in response.data

    def test_login_fails_with_wrong_password(self, api_client, user):
        url = reverse('users_api:token_obtain')
        response = api_client.post(url, {'email': user.email, 'password': 'wrongpassword'})

        assert response.status_code == 401

    def test_login_fails_for_inactive_user(self, api_client):
        User.objects.create_user(
            email='pending@example.com',
            password='supersecret123',
            display_name='Pending User',
            is_active=False,
        )
        url = reverse('users_api:token_obtain')
        response = api_client.post(url, {'email': 'pending@example.com', 'password': 'supersecret123'})

        assert response.status_code == 401