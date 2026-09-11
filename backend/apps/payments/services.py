import stripe
from django.conf import settings
from datetime import datetime, timezone as dt_timezone

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_stripe_customer(user):
    """A Stripe Customer is a separate object from our User — this keeps
    the two linked, creating the Stripe side lazily on first checkout."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(email=user.email, name=user.display_name)
    user.stripe_customer_id = customer.id
    user.save(update_fields=['stripe_customer_id'])
    return customer.id


def create_checkout_session(request, user, tier):
    customer_id = get_or_create_stripe_customer(user)

    subscription_data = None
    creator_profile = getattr(tier.creator, 'creator_profile', None)
    if creator_profile and creator_profile.stripe_account_id:
        account = stripe.Account.retrieve(creator_profile.stripe_account_id)
        if account.get('charges_enabled') and account.get('payouts_enabled'):
            subscription_data = {
                'application_fee_percent': settings.STRIPE_PLATFORM_FEE_PERCENT,
                'transfer_data': {'destination': creator_profile.stripe_account_id},
            }
    # If the creator hasn't finished Stripe onboarding yet, subscription_data
    # stays None — the platform account just holds the funds for now instead
    # of failing the checkout outright.

    return stripe.checkout.Session.create(
        customer=customer_id,
        mode='subscription',
        line_items=[{'price': tier.stripe_price_id, 'quantity': 1}],
        subscription_data=subscription_data,
        success_url=f'{settings.FRONTEND_URL}/profile/{tier.creator_id}?checkout=success',
        cancel_url=f'{settings.FRONTEND_URL}/profile/{tier.creator_id}?checkout=cancelled',
        metadata={
            'subscriber_id': user.id,
            'creator_id': tier.creator_id,
            'tier_id': tier.id,
        },
    )

def upgrade_subscription(subscription, new_tier):
    """
    Modifies the EXISTING Stripe subscription's price instead of creating a
    second one — this is what actually prevents a subscriber from ending up
    with two concurrent, simultaneously-billed subscriptions to the same
    creator. Stripe prorates the difference automatically.
    """
    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    item_id = stripe_sub['items']['data'][0]['id']

    stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        items=[{'id': item_id, 'price': new_tier.stripe_price_id}],
        proration_behavior='create_prorations',
    )

    updated = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    period_end_ts = updated['items']['data'][0]['current_period_end']

    subscription.tier = new_tier
    subscription.pending_tier = None
    subscription.current_period_end = datetime.fromtimestamp(period_end_ts, tz=dt_timezone.utc)
    subscription.save(update_fields=['tier', 'pending_tier', 'current_period_end'])


def schedule_downgrade(subscription, new_tier):
    """Doesn't touch Stripe yet — the swap happens at renewal (see the
    invoice.payment_succeeded webhook handler), so the subscriber keeps
    their current tier's access until the period they already paid for
    actually ends."""
    subscription.pending_tier = new_tier
    subscription.save(update_fields=['pending_tier'])