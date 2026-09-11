from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
import stripe
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.subscriptions.models import Subscription
from apps.tiers.models import Tier

from . import services
from .models import Transaction

stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, tier_id):
        tier = get_object_or_404(Tier, pk=tier_id, is_active=True)
        if tier.creator_id == request.user.id:
            return Response({'detail': 'You cannot subscribe to yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        current = Subscription.objects.filter(
            subscriber=request.user, creator=tier.creator, status=Subscription.Status.ACTIVE,
        ).select_related('tier').first()
        if current is None:
            session = services.create_checkout_session(request, request.user, tier)
            return Response({'action': 'checkout', 'url': session.url})
        if tier.level == current.tier.level:
            return Response({'action': 'unchanged', 'detail': 'You already have this tier.'})
        if tier.level > current.tier.level:
            services.upgrade_subscription(current, tier)
            return Response({'action': 'upgraded'})
        services.schedule_downgrade(current, tier)
        return Response({'action': 'downgrade_scheduled', 'current_period_end': current.current_period_end})


class CreatorStatsView(APIView):
    """Subscriber counts by tier + revenue by month, for the creator's own
    dashboard — the API twin of the old Django-template `creator_stats`."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_creator:
            return Response({'detail': 'Not a creator.'}, status=status.HTTP_403_FORBIDDEN)

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
        return Response({
            'subscriber_counts': [{'tier_name': row['tier__name'], 'count': row['count']} for row in subscriber_counts],
            'monthly_revenue': [{'month': row['month'], 'total': row['total']} for row in monthly_revenue],
        })


class CreatorPayoutsView(APIView):
    """Current Stripe Connect status — is the creator connected, can they
    actually receive payouts yet."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_creator:
            return Response({'detail': 'Not a creator.'}, status=status.HTTP_403_FORBIDDEN)

        profile = request.user.creator_profile
        payouts_enabled = False
        charges_enabled = False
        if profile.stripe_account_id:
            account = stripe.Account.retrieve(profile.stripe_account_id)
            payouts_enabled = account.payouts_enabled
            charges_enabled = account.charges_enabled

        return Response({
            'connected': bool(profile.stripe_account_id),
            'payouts_enabled': payouts_enabled,
            'charges_enabled': charges_enabled,
        })


class CreatorPayoutsConnectView(APIView):
    """Creates (if needed) the creator's Stripe Express account and returns
    a fresh onboarding link — the frontend just redirects the browser
    there, same as the old Django view did with `redirect(account_link.url)`,
    except now it hands the URL back as JSON for React to navigate to."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_creator:
            return Response({'detail': 'Not a creator.'}, status=status.HTTP_403_FORBIDDEN)

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
            refresh_url=f'{settings.FRONTEND_URL}/creator?tab=payouts',
            return_url=f'{settings.FRONTEND_URL}/creator?tab=payouts',
            type='account_onboarding',
        )
        return Response({'url': account_link.url})