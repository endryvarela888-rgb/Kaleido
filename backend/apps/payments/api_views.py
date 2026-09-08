from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.subscriptions.models import Subscription
from apps.tiers.models import Tier
from . import services


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
