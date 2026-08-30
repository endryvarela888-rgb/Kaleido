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
    avatar_position_x = models.PositiveSmallIntegerField(default=50)
    avatar_position_y = models.PositiveSmallIntegerField(default=50)
    is_creator = models.BooleanField(
        default=False,
        help_text='Whether this account can publish content and receive subscriptions.',
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email + password are already required by default

    objects = UserManager()

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

class CreatorProfile(models.Model):
    """
    Extra data that only applies to creator accounts. Kept separate from
    User itself (same reasoning as before): most users will never touch
    these fields, so there's no reason to carry them on every User row.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='creator_profile',
        limit_choices_to={'is_creator': True},
    )
    category = models.ForeignKey(
        'content.Category',
        on_delete=models.SET_NULL,
        related_name='creator_profiles',
        null=True,
        blank=True,
    )
    banner_image = models.ImageField(upload_to='creators/banners/', blank=True, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.display_name} — creator profile'