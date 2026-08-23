from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager required because this project authenticates with email
    instead of username (AbstractUser's default manager assumes username).
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for the whole platform. Both subscribers and creators
    are User rows here — 'is_creator' is a flag, not a separate table, so a
    single account can subscribe to others while also creating content.
    """

    username = None  # dropped in favor of email-based auth
    email = models.EmailField('email address', unique=True)
    display_name = models.CharField(
        max_length=100,
        help_text='Public name shown across the platform.',
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_creator = models.BooleanField(
        default=False,
        help_text='Whether this account can publish content and receive subscriptions.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email + password are already required by default

    objects = UserManager()

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.email