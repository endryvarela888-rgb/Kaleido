from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.subscriptions.models import Subscription
from apps.tiers.models import Tier

from . import services
from .models import Transaction

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

from apps.users.decorators import creator_required

from django.contrib import messages

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request, tier_id):
    tier = get_object_or_404(Tier, pk=tier_id, is_active=True)

    if tier.creator_id == request.user.id:
        return redirect('core:home')

    existing = Subscription.objects.filter(
        subscriber=request.user, creator=tier.creator, status=Subscription.Status.ACTIVE,
    ).select_related('tier').first()

    if existing is None:
        session = services.create_checkout_session(request, request.user, tier)
        return redirect(session.url)

    if tier.level == existing.tier.level:
        messages.info(request, f"You're already subscribed to {tier.name}.")
    elif tier.level > existing.tier.level:
        services.upgrade_subscription(existing, tier)
        messages.success(request, f'Upgraded to {tier.name} — you now have full access.')
    else:
        services.schedule_downgrade(existing, tier)
        messages.info(
            request,
            f'Your plan will switch to {tier.name} on {existing.current_period_end:%B %d, %Y}. '
            f'You keep {existing.tier.name} access until then.',
        )

    return redirect('users:profile', pk=tier.creator_id)                    


def checkout_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('core:home')

    session = stripe.checkout.Session.retrieve(session_id).to_dict()
    creator_id = session.get('metadata', {}).get('creator_id')

    messages.success(request, "You're subscribed! It may take a few seconds to unlock content.")

    if creator_id:
        return redirect('users:profile', pk=creator_id)
    return redirect('core:home')

def checkout_cancel(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('core:home')

    session = stripe.checkout.Session.retrieve(session_id).to_dict()
    creator_id = session.get('metadata', {}).get('creator_id')

    messages.info(request, 'Checkout canceled — no charge was made.')

    if creator_id:
        return redirect('users:profile', pk=creator_id)
    return redirect('core:home')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe calls this endpoint directly (not the user's browser), so it's
    CSRF-exempt — but every event is verified against STRIPE_WEBHOOK_SECRET
    before we trust a single byte of it. Never skip that verification.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    handler = EVENT_HANDLERS.get(event['type'])
    if handler:
        handler(event['data']['object'].to_dict())

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    metadata = session.get('metadata', {})
    subscriber_id = metadata.get('subscriber_id')
    creator_id = metadata.get('creator_id')
    tier_id = metadata.get('tier_id')
    if not (subscriber_id and creator_id and tier_id):
        return

    tier = Tier.objects.filter(pk=tier_id).first()
    if tier is None:
        return

    stripe_subscription_id = session.get('subscription')
    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
    period_end_ts = stripe_sub['items']['data'][0]['current_period_end']
    period_end = datetime.fromtimestamp(period_end_ts, tz=dt_timezone.utc)
    
    subscription, _ = Subscription.objects.update_or_create(
        subscriber_id=subscriber_id,
        creator_id=creator_id,
        status=Subscription.Status.ACTIVE,
        defaults={
            'tier': tier,
            'stripe_subscription_id': stripe_subscription_id,
            'current_period_end': period_end,
        },
    )

    Transaction.objects.create(
        user_id=subscriber_id,
        subscription=subscription,
        amount=tier.price,
        currency='usd',
        status=Transaction.Status.SUCCEEDED,
        stripe_checkout_session_id=session.get('id', ''),
        stripe_payment_intent_id=session.get('payment_intent') or '',
    )


def _handle_invoice_paid(invoice):
    """Fires on renewals. If there's a pending_tier (a scheduled downgrade),
    this is the moment it actually takes effect — the invoice that just got
    paid was still charged at the OLD price, so swapping now only affects
    the period starting from here on."""
    stripe_subscription_id = invoice.get('subscription')
    if not stripe_subscription_id:
        return

    subscription = Subscription.objects.filter(
        stripe_subscription_id=stripe_subscription_id
    ).select_related('pending_tier').first()
    if subscription is None:
        return

    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)

    if subscription.pending_tier_id:
        item_id = stripe_sub['items']['data'][0]['id']
        stripe.Subscription.modify(
            stripe_subscription_id,
            items=[{'id': item_id, 'price': subscription.pending_tier.stripe_price_id}],
            proration_behavior='none',
        )
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        subscription.tier = subscription.pending_tier
        subscription.pending_tier = None

    period_end_ts = stripe_sub['items']['data'][0]['current_period_end']
    subscription.current_period_end = datetime.fromtimestamp(period_end_ts, tz=dt_timezone.utc)
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=['current_period_end', 'status', 'tier', 'pending_tier'])

    Transaction.objects.create(
        user=subscription.subscriber,
        subscription=subscription,
        amount=(invoice.get('amount_paid', 0) or 0) / 100,
        currency=invoice.get('currency', 'usd'),
        status=Transaction.Status.SUCCEEDED,
        stripe_payment_intent_id=invoice.get('payment_intent') or '',
    )


def _handle_subscription_deleted(stripe_sub):
    Subscription.objects.filter(stripe_subscription_id=stripe_sub.get('id')).update(
        status=Subscription.Status.CANCELED,
        canceled_at=timezone.now(),
    )


EVENT_HANDLERS = {
    'checkout.session.completed': _handle_checkout_completed,
    'invoice.payment_succeeded': _handle_invoice_paid,
    'customer.subscription.deleted': _handle_subscription_deleted,
}

@creator_required
def creator_stats(request):
    subscriber_counts = (
        Subscription.objects
        .filter(creator=request.user, status=Subscription.Status.ACTIVE)
        .values('tier__name')
        .annotate(count=Count('id'))
        .order_by('tier__level')
    )

    monthly_revenue = (
        Transaction.objects
        .filter(subscription__creator=request.user, status=Transaction.Status.SUCCEEDED)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('-month')[:12]
    )

    return render(request, 'creator_dashboard/stats.html', {
        'subscriber_counts': subscriber_counts,
        'monthly_revenue': monthly_revenue,
        'active_tab': 'stats',
    })


@creator_required
def creator_payouts(request):
    profile = request.user.creator_profile
    account = None
    if profile.stripe_account_id:
        account = stripe.Account.retrieve(profile.stripe_account_id)
    return render(request, 'creator_dashboard/payouts.html', {
        'profile': profile, 'account': account, 'active_tab': 'payouts',
    })


@creator_required
@require_POST
def creator_payouts_connect(request):
    profile = request.user.creator_profile

    if not profile.stripe_account_id:
        account = stripe.Account.create(
            type='express',
            email=request.user.email,
            capabilities={'transfers': {'requested': True}, 'card_payments': {'requested': True}},
        )
        profile.stripe_account_id = account.id
        profile.save(update_fields=['stripe_account_id'])

    account_link = stripe.AccountLink.create(
        account=profile.stripe_account_id,
        refresh_url=request.build_absolute_uri('/payments/creator/payouts/'),
        return_url=request.build_absolute_uri('/payments/creator/payouts/'),
        type='account_onboarding',
    )
    return redirect(account_link.url)