from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Subscription(models.Model):
    """
    Links a subscriber to a creator through a Tier. Only one row per
    (subscriber, creator) may have status='active' at a time — enforced by
    a conditional unique constraint below, not just app-level logic — so
    upgrading/downgrading always means updating the existing active row,
    never creating a second one.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELED = 'canceled', 'Canceled'
        PAST_DUE = 'past_due', 'Past due'
        EXPIRED = 'expired', 'Expired'

    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
        limit_choices_to={'is_creator': True},
    )
    tier = models.ForeignKey(
        'tiers.Tier',
        on_delete=models.PROTECT,
        related_name='subscriptions',
        help_text='The tier currently granting access.',
    )
    pending_tier = models.ForeignKey(
        'tiers.Tier',
        on_delete=models.SET_NULL,
        related_name='pending_subscriptions',
        null=True,
        blank=True,
        help_text='Set on downgrade: takes effect at current_period_end instead of immediately.',
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    current_period_end = models.DateTimeField(
        help_text='When the currently paid period ends — drives renewal and scheduled downgrades.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(
    default=False,
    help_text='If true, access continues until current_period_end, then the subscription ends.',
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'creator'],
                condition=models.Q(status='active'),
                name='unique_active_subscription_per_creator',
            ),
        ]

    def __str__(self):
        return f'{self.subscriber} → {self.creator} ({self.tier.name}, {self.status})'

    def clean(self):
        super().clean()
        if self.subscriber_id and self.subscriber_id == self.creator_id:
            raise ValidationError('A user cannot subscribe to themselves.')
        if self.tier_id and self.creator_id and self.tier.creator_id != self.creator_id:
            raise ValidationError('The tier must belong to the selected creator.')