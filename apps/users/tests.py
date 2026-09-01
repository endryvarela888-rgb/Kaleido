from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ActivationEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='waiting@example.com',
            password='safe-password-123',
            display_name='Waiting User',
            is_active=False,
        )

    def test_signup_resends_for_an_existing_inactive_account(self):
        response = self.client.post(
            reverse('users:signup'),
            {
                'email': self.user.email,
                'display_name': 'Another name',
                'password1': 'safe-password-123',
                'password2': 'safe-password-123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email=self.user.email).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('activate/', mail.outbox[0].body)

    def test_resend_activation_sends_to_an_inactive_account(self):
        response = self.client.post(
            reverse('users:resend_activation'),
            {'email': self.user.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('activate/', mail.outbox[0].body)
