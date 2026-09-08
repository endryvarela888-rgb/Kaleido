from django.conf import settings
from django.db import models


class Tier(models.Model):
    """
    A subscription level defined by a creator. 'level' drives the access
    hierarchy: a subscriber on level 3 can see content gated at level 1,
    2, or 3 — not just an exact match. Full tier logic (pricing rules,
    benefits) gets fleshed out when we build the tiers app properly；
    this is the minimal shape content.Content needs to reference.
    """

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tiers',
        limit_choices_to={'is_creator': True},
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    level = models.PositiveSmallIntegerField(
        help_text='Hierarchy rank within this creator\'s tiers (1 = lowest).'
    )
    is_active = models.BooleanField(default=True)
    stripe_product_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creator', 'level']
        constraints = [
            models.UniqueConstraint(
                fields=['creator', 'level'],
                condition=models.Q(is_active=True),
                name='unique_active_tier_level_per_creator',
            ),
        ]

    def __str__(self):
        return f'{self.creator} — {self.name} (level {self.level})'