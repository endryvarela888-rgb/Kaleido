from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Same mechanism Django uses for password-reset tokens, reused here for
    email verification. Including `is_active` in the hash means the link
    stops working automatically the moment the account gets activated —
    so an old activation email can't be replayed later.
    """

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{timestamp}{user.is_active}'


account_activation_token = AccountActivationTokenGenerator()