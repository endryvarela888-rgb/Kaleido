import stripe
from django.conf import settings
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY


def cancel_subscription(subscription):
    stripe.Subscription.modify(subscription.stripe_subscription_id, cancel_at_period_end=True)
    subscription.cancel_at_period_end = True
    subscription.pending_tier = None
    subscription.canceled_at = timezone.now()
    subscription.save(update_fields=['cancel_at_period_end', 'pending_tier', 'canceled_at'])

def renew_subscription(subscription):
    """Undoes a scheduled cancellation — only valid while the subscription
    is still ACTIVE with cancel_at_period_end=True (i.e. before the period
    actually ends and Stripe fires customer.subscription.deleted)."""
    stripe.Subscription.modify(subscription.stripe_subscription_id, cancel_at_period_end=False)
    subscription.cancel_at_period_end = False
    subscription.canceled_at = None
    subscription.save(update_fields=['cancel_at_period_end', 'canceled_at'])